"""Publish only verified aggregate evidence; retain every historical result."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .data_ingest import ROOT, digest
from .economic_recovery import missing_contribution_scenarios
from .reconstruction import write_json, price_return_audit
from .stats import performance


def export(workspace, ff3, evidence, replay, backup_receipt):
    workspace, ff3, evidence, replay = map(Path, [workspace,ff3,evidence,replay])
    output=ROOT/'outputs/final'; output.mkdir(exist_ok=True)
    manifest=json.loads((ROOT/'outputs/reconstruction/recollected_input_manifest.json').read_text())
    for row in manifest['files']:
        if digest(workspace/'data/private'/row['file']) != row['sha256']:
            raise ValueError('private source version changed')
    new=pd.read_csv(replay/'recollected_monthly_returns.csv',parse_dates=['date'])
    old=pd.read_csv(ROOT/'snapshots/public-c8abb0f/monthly_returns.csv',parse_dates=['date'])
    change={}
    z=old.merge(new,on='date',suffixes=('_old','_new'),validate='one_to_one')
    for s in ['VFS','Value','Market']:
        change[s]=int((~np.isclose(z[s+'_old'],z[s+'_new'],atol=1e-12,rtol=0,equal_nan=True)).sum())
    if any(change.values()):
        raise ValueError('unexpected return changes require a separately reviewed version')
    rows=[]
    for scope,first,last,strategies in [('VFS_OWN','2021-07-01','2022-02-01',['VFS','Market']),('COMMON','2021-07-01','2021-12-01',['VFS','Value','Market'])]:
        for s in strategies:
            a=performance(old.loc[old.date.between(first,last)],s)
            b=performance(new.loc[new.date.between(first,last)],s)
            rows.append({'scope':scope,'strategy':s,'start':first,'end':last,
                'baseline_n':a['n_months'],'final_n':b['n_months'],
                **{'baseline_'+k:a[k] for k in ['total_return','cagr','mdd']},
                **{'final_'+k:b[k] for k in ['total_return','cagr','mdd']},
                'return_basis':'PRICE_RETURN_ONLY','cost_bps_per_one_way_leg':0,
                'economic_repairs':0,'change_cause':'NO_ECONOMIC_REPAIR_IDENTICAL_SAME_MONTHS'})
    pd.DataFrame(rows).to_csv(output/'baseline_vs_final.csv',index=False)
    gaps=pd.read_csv(ROOT/'outputs/reconstruction/recollected_held_gap_diagnosis.csv')
    gaps.to_csv(output/'held_gap_audit_public.csv',index=False)
    scenarios=missing_contribution_scenarios(gaps)
    scenarios.to_csv(output/'missing_exposure_scenarios.csv',index=False)
    findings=json.loads((ROOT/'config/economic_event_findings.json').read_text())['events']
    sections=pd.read_csv(evidence/'section_inventory.csv',dtype={'receipt':str})
    if set(sections.event_id)!=set(r['event_id'] for r in findings) or not sections.status.eq('BODY_AVAILABLE').all():
        raise ValueError('all 11 events require readable official evidence')
    public=sections.rename(columns={'receipt':'rcept_no','section':'official_section','status':'access_status'})
    public['verification_level']='OFFICIAL_BODY_READ_EVENT_FACTS_ONLY_NOT_MONTHLY_PAYOFF'
    public.to_csv(output/'event_evidence_register.csv',index=False)
    repair=pd.DataFrame(findings)
    repair['return_status']='UNVERIFIED';repair['repaired']=False
    repair['verified_month_boundary_valuation']=False
    repair['source_original_modified']=False
    repair.to_csv(output/'return_repair_status.csv',index=False)
    alpha=pd.read_csv(ROOT/'outputs/ff3_alphas.csv');alpha['analysis_type']='FF3_HAC'
    robust=pd.read_csv(ROOT/'outputs/robustness.csv');robust['analysis_type']='LOCKED_ROBUSTNESS';robust['status']=robust.alpha_status
    neutral=pd.read_csv(ROOT/'outputs/reconstruction/exploratory_g_neutral_alpha.csv');neutral['analysis_type']='EXPLORATORY_G_NEUTRAL'
    pd.concat([alpha,robust,neutral],ignore_index=True).to_csv(output/'robustness_and_alpha_status.csv',index=False)
    source=price_return_audit(pd.read_parquet(ff3/'data/stock_returns.parquet'),pd.read_parquet(ff3/'data/market_data_long.parquet'))
    missing=source.loc[source['return'].isna()]
    def categories(q):
        current_absent=q.value.isna();previous_absent=q.unfiltered.isna()&~current_absent
        extreme=q.gt100_filtered
        unexplained=~current_absent&~previous_absent&~extreme
        return {'missing':len(q),'current_price_absent':int(current_absent.sum()),
                'previous_price_or_first_observation_unavailable':int(previous_absent.sum()),
                'extreme_filter':int(extreme.sum()),'other_source_gap':int(unexplained.sum()),
                'classification':'EXCLUSIVE_SOURCE_FIELDS_NOT_VERIFIED_CORPORATE_ACTION_CAUSES'}
    full=categories(missing);study=categories(missing.loc[missing.date.between('2016-01-01','2026-04-01')])
    write_json(output/'source_missingness_types.json',{'full_source':full,'study_2016_01_to_2026_04':study,
        'all_659_filtered_positive':bool(source.loc[source.gt100_filtered,'unfiltered'].gt(1).all()),
        'filtered_are_subset_of_missing':True,'officially_verified_errors':0})
    checks={f:digest(replay/f)==digest(ROOT/'outputs/reconstruction'/f) for f in [
        'recollected_monthly_returns.csv','recollected_performance_summary.csv',
        'recollected_vfs_strategy_summary.csv','recollected_robustness.csv','exploratory_g_neutral_monthly.csv']}
    if not all(checks.values()):raise ValueError('offline replay aggregate regression failure')
    receipt=json.loads((evidence/'collection_receipt.json').read_text())
    backup=json.loads(Path(backup_receipt).read_text())
    if backup['hash_failures']!=0 or backup['credentials_included']:
        raise ValueError('owner backup hash/security validation failed')
    write_json(output/'raw_replay_validation.json',{'status':'PASS_CURRENT_SOURCE_OFFLINE_RERUN',
        'credentials_used_for_replay':False,'source_manifest':'../reconstruction/recollected_input_manifest.json',
        'aggregate_csv_bytes_identical':checks,'monthly_changes_above_1e_12':change,
        'historical_receipt_documents':int(sections.receipt.nunique()),'readable_sections':len(sections),
        'public_web_requests':receipt['total_cached_public_web_requests'],
        'official_historical_prices_access':'BLOCKED_ACCESS_KRX_UI_REQUIRES_LOGIN',
        'official_terms_do_not_prove_month_end_valuation':True,
        'backup_rehash_files':backup['file_count'],'backup_rehash_bytes':backup['bytes'],
        'backup_rehash_failures':backup['hash_failures']})
    status={'classification':'COMPLETE_LIMITED_EVIDENCE','empirical_status':'EMPIRICAL_LIMITED',
        'basis':'11_EVENTS_OFFICIAL_BODIES_READ_CURRENT_SOURCES_RERUN_AND_LIMITS_PUBLISHED',
        'unique_held_security_months':11,'strategy_security_records':13,
        'official_documents':int(sections.receipt.nunique()),'official_sections':len(sections),
        'economic_returns_repaired':0,'vfs_own_contiguous_months':8,'paired_contiguous_months':6,
        'g_neutral_contiguous_months':2,'primary_alpha':'NOT_ESTIMATED',
        'independent_oos':'UNVERIFIED','long_investable_strategy_verified':False,
        'source_security_rows_uploaded':False,'primary_design_changed':False,
        'unresolved':['Verified month-boundary quantity/cash/price and adjustment basis',
                      'June formation tradability for E04/E07',
                      'Cash entitlement timing may affect December 2021 diagnostic marks',
                      '2016-2020 joint PIT G and financial coverage',
                      'Historical exchange-wide universe and corrected-filing vintage',
                      'MSCI G equivalence, dividends, delisting payoffs, independent OOS'],
        'blocked_access':['Official historical KRX price query requires login; no access bypass',
                          'FnGuide redistribution rights unverified; no source uploads'],
        'publication':{'pr_state':'VALIDATED_LOCAL_PENDING_PR','main_ci':'PENDING_NEW_COMMIT','pages':'PENDING_NEW_COMMIT'}}
    write_json(output/'completion_status.json',status)
    figures=output/'figures';figures.mkdir(exist_ok=True)
    plt.rcParams.update({'svg.fonttype':'none','font.size':10})
    fig,ax=plt.subplots(figsize=(8,4.2))
    fig.subplots_adjust(left=.12,right=.98,top=.88,bottom=.19)
    for s,color in [('VFS','#285f93'),('Value','#ba713d')]:
        q=gaps.loc[gaps.strategy.eq(s)]
        ax.plot(pd.to_datetime(q.date),q.missing_weight*100,'o',label=s,color=color)
    ax.set(title='Observed unknown position exposure at first annual break',ylabel='Pre-break portfolio weight (%)')
    ax.legend();ax.grid(alpha=.2)
    fig.text(.02,.02,'2022-01 to 2025-09 | 10 strategy break months / 13 positions / 11 unique events | gross price paths',fontsize=7.5)
    fig.savefig(figures/'held_gap_exposure.svg');fig.savefig(figures/'held_gap_exposure.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4.6))
    fig.subplots_adjust(left=.12,right=.98,top=.86,bottom=.34)
    labels=[r.strategy+' '+r.date[:7] for r in gaps.itertuples()]
    for a in [-1.,-.5,.5,1.]:
        q=scenarios.loc[scenarios.assumed_asset_return.eq(a)]
        ax.plot(np.arange(len(q)),q.unknown_position_contribution_pp,'o',label=f'Assume asset {a*100:+.0f}%')
    ax.set_xticks(np.arange(len(labels)),labels,rotation=45,ha='right')
    ax.set(title='ASSUMPTION ONLY: unknown-position contribution, no NAV extension',ylabel='Isolated portfolio contribution (pp)')
    ax.axhline(0,color='#89919b',lw=.7);ax.legend(ncol=2,fontsize=8);ax.set_facecolor('#fff5e6')
    fig.text(.01,.02,'Not observed returns, confidence intervals, or bounds. Returns >100% remain possible. No imputed portfolio returns.',fontsize=7.3)
    fig.savefig(figures/'missing_scenarios.svg');fig.savefig(figures/'missing_scenarios.png',dpi=180);plt.close(fig)
    for svg in figures.glob('*.svg'):
        svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    return status


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ['workspace','ff3-root','evidence','replay','backup-receipt']:p.add_argument('--'+name,required=True)
    a=p.parse_args();print(json.dumps(export(a.workspace,a.ff3_root,a.evidence,a.replay,a.backup_receipt)))
