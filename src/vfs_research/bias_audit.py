import json
import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests
from .data_ingest import ROOT,paths
from .backtest import run,longest_block
from .factors import load_factors
from .stats import regression,performance


def audit_all():
    legacy,_=paths();p=pd.read_parquet(ROOT/'data/private/pit_panel.parquet');f=load_factors(legacy)
    d=pd.read_csv(ROOT/'outputs/monthly_returns.csv',parse_dates=['date']);primary=d.loc[d.primary_window]
    specs={'equal_weight':{'equal_weight':True},'exclude_universe_top5':{'exclude_top5':True},'g_cut_30':{'g_quantile':.3},'g_cut_70':{'g_quantile':.7},'delay_one_month':{'formation_month':8},'stale_365':{'stale_days':365},'size_neutral_G':{'size_neutral':True},'kospi_reported_only':{'kospi_only':True},'legacy_FF3':{}}
    rows=[]
    for name,kwargs in specs.items():
        fac=load_factors(legacy,'legacy_compatible') if name=='legacy_FF3' else f
        z,_,_=run(p,fac,**kwargs);window=longest_block(z)
        q=z.loc[z.date.isin(window)].merge(fac,on='date',validate='one_to_one')
        alpha=regression(q,'spread')
        same=z.loc[z.date.isin(primary.date)]
        comparable=len(same)>0 and same.common_valid.all()
        rows.append({'spec_id':name,'role':'EXPLORATORY_SENSITIVITY_NOT_NEW_PRIMARY','valid_common_months':int(z.common_valid.sum()),'longest_months':len(window),'window_start':str(window[0].date()) if window else '', 'window_end':str(window[-1].date()) if window else '', 'same_primary_months_valid':bool(comparable),'primary_window_mean_spread':float(same.spread.mean()) if comparable else np.nan,'alpha':alpha['alpha'],'p_hac':alpha['p_hac'],'alpha_status':alpha['status']})
    for bps in [10,30]:
        q=primary.copy();q['VFS']=q[f'VFS_net_{bps}bp'];q['Value']=q[f'Value_net_{bps}bp'];q['spread']=q.VFS-q.Value
        a=regression(q,'spread');ok=q[['VFS','Value']].notna().all().all()
        rows.append({'spec_id':f'cost_{bps}bp','role':'EXPLORATORY_COST_ASSUMPTION','valid_common_months':int(q[['VFS','Value']].notna().all(axis=1).sum()),'longest_months':len(q) if ok else 0,'window_start':str(q.date.min().date()),'window_end':str(q.date.max().date()),'same_primary_months_valid':bool(ok),'primary_window_mean_spread':float(q.spread.mean()) if ok else np.nan,'alpha':a['alpha'],'p_hac':a['p_hac'],'alpha_status':a['status']})
    rob=pd.DataFrame(rows);rob['p_holm']=np.nan
    valid=rob.p_hac.notna()
    if valid.any():rob.loc[valid,'p_holm']=multipletests(rob.loc[valid,'p_hac'],method='holm')[1]
    rob.to_csv(ROOT/'outputs/robustness.csv',index=False)
    checks=[
      ('public_disclosure_timing','PASS','raw G/BE hashes and receipt dates rechecked; every eligible formation precedes return'),
      ('original_disclosure_before_correction','UNVERIFIED','current retrieval vintage; original pre-amendment values unavailable'),
      ('historical_exchange_universe','UNVERIFIED','original panel is not certified exchange-wide historical membership'),
      ('terminal_delisting_payoff','UNVERIFIED','no terminal-return imputation; holdings path stops on missing return'),
      ('missing_held_return_handling','PASS','no zero fill or ex-post reweight; annual path invalidated'),
      ('cash_dividend_total_return','UNVERIFIED','PRICE_RETURN_ONLY; source arithmetic reproduces raw price pct_change'),
      ('corporate_actions_gt100_filter','UNVERIFIED','659 observations historically filtered; no unsupported repair'),
      ('financial_PIT_scope','PASS','BE matched to official receipt, currency and account scope; correction vintage separately unverified'),
      ('G_proxy_statutory_size_confound','UNVERIFIED','outside-director ratio is one proxy; consolidated assets cannot certify statutory separate-entity threshold'),
      ('historical_sector_ROE_momentum_liquidity','UNVERIFIED','PIT ROE descriptive exposure only; sector, liquidity, dividends and causal controls incomplete'),
      ('formation_weight_caps','PASS','cell weights <=25%, final VFS <=12.5% at formation; annual drift reported'),
      ('execution_costs','UNVERIFIED','0/10/30bp assumed per one-way trade; liquidity, taxes, suspended execution and unknown reset turnover unresolved'),
      ('parameter_lock','PASS','design lock committed before new VFS outcome viewing; all registered sensitivity results retained'),
      ('independent_OOS','UNVERIFIED','all history exposed to earlier study; no independent holdout'),
      ('statistical_sample_size','FAIL','6 contiguous common months <24; FF3/HAC alpha intentionally NA'),
      ('coverage_selection','UNVERIFIED','financial/G matching nonrandom; valid-month selection itself has availability bias')]
    pd.DataFrame(checks,columns=['check','status','evidence_and_remaining_risk']).to_csv(ROOT/'outputs/bias_audit.csv',index=False)
    # Contemporary disclosure observations; no current industry is backfilled.
    selected=p.loc[p.date.dt.month.eq(7)&p.joint_eligible].copy()
    selected['log_ME']=np.log(selected.lag_me);selected['year']=selected.date.dt.year
    diag=[]
    for year,q in selected.groupby('year'):
        diag.append({'year':year,'n':len(q),'G_log_ME_correlation':q.g_value.corr(q.log_ME),'G_tie_at_median_fraction':q.g_value.eq(q.g_value.median()).mean(),'median_G':q.g_value.median(),'ROE_available_n':q.roe.notna().sum(),'consolidated_assets_2tn_mean_G':q.loc[q.total_assets_krw.ge(2e12),'g_value'].mean(),'other_mean_G':q.loc[q.total_assets_krw.lt(2e12),'g_value'].mean(),'statutory_separate_entity_threshold':'UNVERIFIED'})
    pd.DataFrame(diag).to_csv(ROOT/'outputs/size_G_diagnostics.csv',index=False)
    status=json.loads((ROOT/'outputs/results_status.json').read_text());status['bias_audit_counts']=pd.Series([s for _,s,_ in checks]).value_counts().to_dict();status['robustness_specifications']=len(rows);status['holm_estimable_tests']=int(valid.sum())
    (ROOT/'outputs/results_status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')
    from .control_diagnostics import build_control_diagnostics
    build_control_diagnostics()
    print(json.dumps({'audit_counts':status['bias_audit_counts'],'sensitivity_specs':len(rows),'estimable_alphas':int(valid.sum())}))
