"""Validate real published aggregates without redistributing private input rows."""
import json
import numpy as np
import pandas as pd
import pytest
from vfs_research.data_ingest import ROOT, digest
from vfs_research.stats import performance


def test_original_snapshots_engine_and_primary_design_are_preserved():
    manifest=json.loads((ROOT/'snapshots/public-c8abb0f/manifest.json').read_text())
    for row in manifest['files']:
        assert digest(ROOT/row['snapshot'])==row['sha256']
    for path in ['config/vfs_pre_analysis_plan.yaml','config/design_lock.json','src/vfs_research/backtest.py','src/vfs_research/portfolio.py','reports/RESEARCH_REPORT.pdf','reports/RESEARCH_REPORT.md']:
        assert digest(ROOT/path)==manifest['protected_artifact_hashes'][path]


def test_recollected_metrics_and_change_counts_are_recomputed():
    out=ROOT/'outputs/reconstruction'
    if not (out/'raw_replay_summary.json').exists():
        pytest.skip('collection not yet completed')
    new=pd.read_csv(out/'recollected_monthly_returns.csv',parse_dates=['date'])
    old=pd.read_csv(ROOT/'snapshots/public-c8abb0f/monthly_returns.csv',parse_dates=['date'])
    summary=json.loads((out/'raw_replay_summary.json').read_text())
    assert summary['old_private_files_used'] is False
    assert summary['economic_returns_repaired']==0
    joined=old.merge(new,on='date',suffixes=('_old','_new'),validate='one_to_one')
    for strategy in ['VFS','Value','Market']:
        changes=int((~np.isclose(joined[strategy+'_old'],joined[strategy+'_new'],rtol=0,atol=1e-12,equal_nan=True)).sum())
        assert changes==summary['changed_monthly_returns_above_1e_12'][strategy]
    for row in pd.read_csv(out/'recollected_performance_summary.csv').itertuples():
        actual=performance(new.loc[new.primary_window],row.strategy)
        assert row.n_months==actual['n_months']
        for name in ['total_return','mdd','sharpe']:
            assert np.isclose(getattr(row,name),actual[name],rtol=0,atol=1e-12)
    gaps=pd.read_csv(out/'recollected_held_missing_monthly.csv')
    assert int(gaps.missing_held_securities.sum())==summary['held_missing_records']
    receipt=json.loads((out/'restoration_validation.json').read_text())
    assert receipt['status']=='PASS_OWNER_LOCAL_BACKUP_OFFLINE_RAW_REPLAY'
    assert receipt['backup_hash_failures_after_restore']==0
    assert receipt['credentials_required_for_replay'] is False
    for name,sha in receipt['aggregate_csv_bytes_identical'].items():
        assert digest(out/name)==sha


def test_recollected_inference_respects_minimum_and_locked_followup():
    out=ROOT/'outputs/reconstruction'
    for file,lock in [('public_rebuild_followup_plan.yaml','public_rebuild_followup_lock.json'),('public_rebuild_multiplicity_addendum.yaml','public_rebuild_multiplicity_addendum_lock.json')]:
        assert digest(ROOT/'config'/file)==json.loads((ROOT/'config'/lock).read_text())['sha256']
    if not (out/'followup_multiplicity.csv').exists():
        pytest.skip('replay not yet completed')
    results=pd.read_csv(out/'followup_multiplicity.csv')
    assert len(results)==8
    short=results.loc[results.n_months.lt(24)]
    assert short.status.eq('NOT_ESTIMATED').all()
    assert short[['alpha','p_hac','ci_low','ci_high','p_holm']].isna().all().all()
