import argparse,hashlib,json,sys
from datetime import datetime,timezone
import numpy as np
import pandas as pd
import yaml
from .data_ingest import ROOT,paths,load_panel,return_audit,digest,load_benchmark
from .factors import load_factors
from .backtest import run,longest_block
from .stats import regression,performance,block_bootstrap_mean


def write_json(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def config():
    p=ROOT/'config/vfs_pre_analysis_plan.yaml'
    lock=json.loads((ROOT/'config/design_lock.json').read_text())
    if digest(p)!=lock['sha256']:raise ValueError('design changed after lock')
    return yaml.safe_load(p.read_text())


def gate_a():
    p,g,f,evidence=load_panel();legacy,ff3=paths();benchmark=load_benchmark(ff3)
    returns,cells,formation=run(p,benchmark)
    dates=longest_block(returns);valid=int(returns.common_valid.sum())
    coverage=p.groupby('date').agg(population_n=('stock_code','size'),g_pit_n=('G_PIT','sum'),financial_pit_n=('financial_PIT','sum'),joint_n=('joint_eligible','sum'),missing_return_n=('return',lambda x:x.isna().sum())).reset_index()
    coverage=coverage.loc[coverage.date.between('2016-01-01','2026-04-01')]
    coverage['original_period']='2016-01~2026-04';coverage['return_basis']='PRICE_RETURN_ONLY';coverage['dividend_status']='UNVERIFIED';coverage['delisting_status']='UNVERIFIED'
    coverage=coverage.merge(returns[['date','common_valid','VFS_reason','Value_reason']],on='date')
    coverage.to_csv(ROOT/'data_quality/coverage_matrix.csv',index=False);coverage.to_csv(ROOT/'outputs/coverage_matrix.csv',index=False)
    cells.to_csv(ROOT/'outputs/cell_formation_coverage.csv',index=False)
    annual=g.groupby('bsns_year').agg(g_verified_n=('stock_code','size'),companies=('stock_code','nunique')).reset_index()
    annual.to_csv(ROOT/'data_quality/governance_year_coverage.csv',index=False)
    info={**evidence,**return_audit(ff3),'common_valid_months':valid,'longest_common_contiguous_months':len(dates),'available_window':[str(d.date()) for d in (dates[0],dates[-1])] if dates else [],'gate_a':'PASS_DIAGNOSTIC_ONLY' if dates else 'FAIL','investable_total_return_validation':'UNVERIFIED','alpha_feasibility':len(dates)>=24,'cutoff':'2026-04'}
    write_json(ROOT/'outputs/gate_a.json',info)
    (ROOT/'docs/GATE_A.md').write_text('# GATE A - actual input diagnostic\n\n'+json.dumps(info,ensure_ascii=False,indent=2)+'\n\nThe engine has genuine estimable diagnostic months, so limited-result presentation is permitted. A full-period investable backtest is not established. Required historical financial/G evidence is absent before 2021. No missing month is dropped or filled. A missing held return invalidates the annual path until the next formation; future survivors are never selected. The window is selected from availability, not observed returns. Annual holding weights drift between rebalances. Original current-listing selection and correction-vintage risks remain unresolved.\n\n[Access attempts](data_access_probes.json), [coverage](../data_quality/coverage_matrix.csv), [raw snapshot verification](../outputs/gate_a.json). FnGuide row-level data and API responses remain local only. Aggregates are independently authored analysis; provider rights in source data remain unverified.\n')
    print(json.dumps(info,ensure_ascii=False))


def design_lock():
    p=ROOT/'config/vfs_pre_analysis_plan.yaml';h=digest(p);f=ROOT/'config/design_lock.json'
    if f.exists():
        if json.loads(f.read_text())['sha256']!=h:raise ValueError('refuse overwrite design lock')
        return
    write_json(f,{'sha256':h,'locked_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'before new VFS outcome estimation; prior FF3 G pilot known','outcome_viewed':False})
    (ROOT/'config/locked_design.sha256').write_text(h+'  vfs_pre_analysis_plan.yaml\n')
    (ROOT/'docs/DECISIONS.md').write_text('# Append-only decisions\n\nD001: prior FF3 governance results known; this study is exploratory. GATE A inspects source evidence and availability only. July annual formation, median ties, strict missing-return path and no winsorization are locked before new VFS outcomes.\nD002: caps apply at formation. Annual buy-and-hold can exceed 12.5% between rebalances; realized drift is disclosed rather than secretly monthly rebalanced.\nD003: evidence does not support the original 2016-2026 horizon, total return or independent OOS. Do not shrink universe after seeing missing returns.\n')
    print('DESIGN_LOCKED',h)


def data_build():
    config();p,g,f,info=load_panel()
    p=p.loc[p.date.le(pd.Timestamp('2026-04-01'))]
    p.to_parquet(ROOT/'data/private/pit_panel.parquet',index=False)
    write_json(ROOT/'outputs/input_snapshot.json',info)
    print('PIT_DATA_BUILT',len(p))


def backtest():
    config();legacy,ff3=paths();p=pd.read_parquet(ROOT/'data/private/pit_panel.parquet');benchmark=load_benchmark(ff3)
    d,c,h=run(p,benchmark);window=longest_block(d)
    gate=json.loads((ROOT/'outputs/gate_a.json').read_text())
    assert len(window)==gate['longest_common_contiguous_months']
    d['primary_window']=d.date.isin(window)
    d=d.merge(benchmark[['date','rf']],on='date',how='left',validate='one_to_one');d.to_csv(ROOT/'outputs/monthly_returns.csv',index=False)
    c.to_csv(ROOT/'outputs/cell_formation_coverage.csv',index=False);h.to_csv(ROOT/'outputs/formation_summary.csv',index=False)
    q=d.loc[d.primary_window]
    perf=[performance(q,s) for s in ['VFS','Value','Market']] if len(q) else []
    pd.DataFrame(perf).to_csv(ROOT/'outputs/performance_summary.csv',index=False)
    # Entire incomplete calendar years are NA, never sum only surviving months.
    years=[]
    for year,z in d.groupby(d.date.dt.year):
        for s in ['VFS','Value','Market']:
            ok=z[s].notna().all() and len(z)==12
            years.append({'year':year,'strategy':s,'valid_months':int(z[s].notna().sum()),'return':float((1+z[s]).prod()-1) if ok else np.nan,'status':'COMPLETE_CALENDAR_YEAR' if ok else 'NOT_ESTIMATED_INCOMPLETE_YEAR'})
    pd.DataFrame(years).to_csv(ROOT/'outputs/annual_returns.csv',index=False)
    status={'final_status':'EMPIRICAL_LIMITED','research_role':'exploratory','return_basis':'PRICE_RETURN_ONLY','original_period':'2016-01~2026-04','primary_start':str(q.date.min().date()) if len(q) else None,'primary_end':str(q.date.max().date()) if len(q) else None,'primary_n_months':len(q),'common_valid_months':int(d.common_valid.sum()),'joint_companies':gate['joint_companies'],'joint_observations':gate['joint_observations'],'independent_oos':'UNVERIFIED','full_investable_backtest':'NOT_VERIFIED','primary_alpha':'NOT_ESTIMATED' if len(q)<24 else 'EXPLORATORY','gate_a':gate['gate_a'],'gate_b':'PASS_WITH_DOCUMENTED_ADAPTATIONS','gate_c':'LOCKED_EXPLORATORY','gate_d_f':'FAIL_MIN24' if len(q)<24 else 'EMPIRICAL_LIMITED','gate_e':'MATERIAL_BIASES_UNVERIFIED','gate_g_r_h':'PENDING','blockers':['Missing held returns break annual holdings paths','No verified dividend/corporate-action/delisting payoffs','Historical exchange-wide universe unverified','No independent OOS','Original-before-correction disclosure vintage unverified']}
    status_path=ROOT/'outputs/results_status.json'
    previous=json.loads(status_path.read_text()) if status_path.exists() else {}
    for key in ['gate_g','gate_r','gate_h','new_repo_ci','dashboard_url','cleanup_pr','portfolio_pr','cleanup_pr_merged','portfolio_pr_merged','source_ff3_head','separation_status','original_full_US_suite']:
        if key in previous:status[key]=previous[key]
    status.update(research_focus='VFS_PORTFOLIO_BACKTEST',ff3_role='SUPPLEMENTARY_ATTRIBUTION',vfs_valid_months=int(d.VFS.notna().sum()))
    own=d.assign(vfs_valid=d.VFS.notna()&d.Market.notna());own_dates=longest_block(own,'vfs_valid')
    status.update(vfs_longest_contiguous_months=len(own_dates),vfs_history_status='PARTIAL_OBSERVED_PRICE_HISTORY',vfs_window_start=str(own_dates[0].date()) if own_dates else None,vfs_window_end=str(own_dates[-1].date()) if own_dates else None)
    write_json(status_path,status)
    print(json.dumps(status,ensure_ascii=False))


def factor_test():
    config();legacy,_=paths();d=pd.read_csv(ROOT/'outputs/monthly_returns.csv',parse_dates=['date'])
    factors=load_factors(legacy).drop(columns=['rf'])
    d=d.merge(factors,on='date',how='left',validate='one_to_one');d.to_csv(ROOT/'outputs/factor_test_inputs.csv',index=False);q=d.loc[d.primary_window]
    rows=[regression(q,s,hac=h) for h in [3,6] for s in ['VFS','Value','spread']]
    pd.DataFrame(rows).to_csv(ROOT/'outputs/ff3_alphas.csv',index=False)
    pd.DataFrame([regression(q,'spread',mean_only=True)]).to_csv(ROOT/'outputs/paired_mean_test.csv',index=False)
    pd.DataFrame(rows)[['strategy','hac_lags','status','beta_mkt','beta_smb','beta_hml']].to_csv(ROOT/'outputs/factor_exposure.csv',index=False)
    write_json(ROOT/'outputs/bootstrap.json',{str(b):block_bootstrap_mean(q.spread,block=b) for b in [6,12]})
    print('FF3_ROWS',len(rows),'ESTIMATED',sum(r['status']!='NOT_ESTIMATED' for r in rows))


def audit():
    from .bias_audit import audit_all
    audit_all()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['gate-a','design-lock','data-build','backtest','factor-test','audit','figures','report','verify-public']);args=parser.parse_args()
    if args.command in ['figures','report','verify-public']:
        from . import reporting
        getattr(reporting,args.command.replace('-','_'))()
    else:globals()[args.command.replace('-','_')]()


if __name__=='__main__':main()
