"""Replay an already implemented strategy into a separate current-vintage folder."""
import argparse
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

import numpy as np
import pandas as pd

from .data_ingest import ROOT, digest
from .portfolio import make_weights, step
from .sorts import classify
from .universe import eligible
from .backtest import longest_block
from .factors import load_factors
from .reconstruction import g_neutral_weights, write_json, price_return_audit, public_audit
from .stats import regression, performance


def holdings_gaps(panel, private):
    """Identify both strategies' first annual path break, with unchanged rules."""
    held = {'VFS': None, 'Value': None}
    broken = {'VFS': False, 'Value': False}
    events = []
    for date in pd.date_range('2016-01-01', '2026-04-01', freq='MS'):
        current = panel.loc[panel.date.eq(date)]
        if date.month == 7:
            q = eligible(current)
            q = q.loc[(q.formation_month_end - q.filing_date).dt.days.le(550)]
            held, _ = make_weights(classify(q))
            broken = {s: held[s] is None for s in held}
        realized = current.set_index('stock_code')['return']
        for strategy, weights in held.items():
            if weights is None or broken[strategy]:
                continue
            missing = realized.reindex(weights.index).isna()
            if missing.any():
                for stock in weights.index[missing]:
                    events.append({'date': date, 'strategy': strategy, 'stock_code': stock,
                                   'held_weight_before_break': float(weights[stock]),
                                   'economic_return_repair': 'UNVERIFIED_NO_CORRECTION'})
            try:
                _, held[strategy] = step(weights, realized)
            except ValueError:
                broken[strategy] = True
    detail = pd.DataFrame(events, columns=['date','strategy','stock_code','held_weight_before_break','economic_return_repair'])
    detail.to_csv(Path(private) / 'held_missing_returns.csv', index=False)
    return detail.groupby(['date', 'strategy']).size().rename('missing_held_securities').reset_index()


def diagnose_held_gaps(workspace, ff3, output):
    detail = pd.read_csv(workspace / 'data/private/held_missing_returns.csv', dtype={'stock_code':str}, parse_dates=['date'])
    detail['code'] = 'A' + detail.stock_code
    prices = price_return_audit(pd.read_parquet(ff3/'data/stock_returns.parquet'), pd.read_parquet(ff3/'data/market_data_long.parquet'))
    detail = detail.merge(prices[['code','date','return','value','unfiltered','gt100_filtered']], on=['code','date'], how='left', indicator='source_join', validate='many_to_one')
    detail['raw_price_missing'] = detail.value.isna()
    detail['source_row_missing'] = detail.source_join.eq('left_only')
    detail['gt100_filtered'] = detail.gt100_filtered.fillna(False).astype(bool)
    detail['unclassified_missing'] = ~detail.raw_price_missing & ~detail.gt100_filtered
    detail.to_csv(workspace/'data/private/held_gap_source_diagnosis.csv',index=False)
    aggregate = detail.groupby(['date','strategy']).agg(missing_held_securities=('stock_code','size'), missing_weight=('held_weight_before_break','sum'), raw_price_missing=('raw_price_missing','sum'), source_row_missing=('source_row_missing','sum'), gt100_filtered=('gt100_filtered','sum'), unclassified_missing=('unclassified_missing','sum')).reset_index()
    aggregate['economic_payoff_verification']='UNVERIFIED_ZERO_CORRECTIONS'
    aggregate.to_csv(output/'recollected_held_gap_diagnosis.csv',index=False)
    audit=json.loads((output/'return_audit_summary.json').read_text())
    audit.update(held_security_attribution='COMPLETED_FOR_BOTH_RECOLLECTED_STRATEGIES', held_missing_records=len(detail), held_gt100_filtered=int(detail.gt100_filtered.sum()), held_raw_price_missing=int(detail.raw_price_missing.sum()))
    write_json(output/'return_audit_summary.json',audit)
    return aggregate


def run(workspace, ff3, output, run_name='vfs-vintage-run'):
    workspace, ff3, output = Path(workspace).resolve(), Path(ff3).resolve(), Path(output).resolve()
    plan = ROOT / 'config/public_rebuild_followup_plan.yaml'
    lock = json.loads((ROOT / 'config/public_rebuild_followup_lock.json').read_text())
    if digest(plan) != lock['sha256']:
        raise ValueError('follow-up plan changed after lock')
    addendum = ROOT / 'config/public_rebuild_multiplicity_addendum.yaml'
    if digest(addendum) != json.loads(addendum.with_name('public_rebuild_multiplicity_addendum_lock.json').read_text())['sha256']:
        raise ValueError('multiplicity addendum changed after lock')
    if not run_name.startswith('vfs-vintage-run') or Path(run_name).name != run_name:
        raise ValueError('invalid isolated run name')
    run_root = workspace / run_name
    if run_root.exists():
        raise ValueError('vintage run already exists; preserve it and choose a new version')
    run_root.mkdir(mode=0o700)
    archive = subprocess.check_output(['git', '-C', str(ROOT), 'archive', 'c8abb0fd648df9eed6b80250cd25b96ca67963b2'])
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:') as tar:
        tar.extractall(run_root, filter='data')
    # Compatibility repair in supplementary cost audit only: the primary CSV
    # deliberately has no SMB/HML columns after the price-backtest separation.
    shutil.copyfile(ROOT/'src/vfs_research/bias_audit.py',run_root/'src/vfs_research/bias_audit.py')
    for name in ['ff3_factors_spec_aligned.csv', 'ff3_factors_legacy_compatible.csv']:
        shutil.copyfile(ROOT / 'legacy_governance_pilot/output' / name, workspace / 'output' / name)
    env = os.environ.copy()
    env.update(VFS_LEGACY_ROOT=str(workspace), VFS_FF3_ROOT=str(ff3), PYTHONPATH=str(run_root / 'src'))
    env.pop('DART_API_KEY', None)
    env.pop('OPENDART_API_KEY', None)
    (run_root / 'data/private').mkdir(parents=True, exist_ok=True)
    for command in ['gate-a', 'design-lock', 'data-build', 'backtest', 'factor-test', 'audit', 'figures']:
        subprocess.run([sys.executable, '-m', 'vfs_research.cli', command], cwd=run_root, env=env, check=True)
    # The baseline loader has a fixed 2026-10-09 description. Correct only this
    # separate run's provenance, without changing any source values or strategy.
    requests = pd.read_csv(workspace / 'data/api_log_sanitized.csv')
    dates = pd.to_datetime(requests.collected_at, utc=True)
    vintage = {'collection_window_utc': [dates.min().isoformat(), dates.max().isoformat()],
               'current_snapshot_revisions': 'current_official_retrieval_original_before_correction_unverified',
               'live_DART_refresh': 'AUTHENTICATED_RECOLLECTION_THEN_OFFLINE_BACKTEST',
               'baseline_fixed_provenance_label_corrected_in_separate_run': True}
    for name in ['input_snapshot.json', 'gate_a.json']:
        file = run_root / 'outputs' / name
        info = json.loads(file.read_text())
        info.update(vintage)
        write_json(file, info)
    output.mkdir(parents=True, exist_ok=True)
    if not (output/'return_audit_summary.json').exists():
        public_audit(ff3,output,workspace/'audit_private')
    evidence = json.loads((run_root / 'outputs/input_snapshot.json').read_text())
    old_evidence = json.loads((ROOT / 'snapshots/public-c8abb0f/input_snapshot.json').read_text())
    monthly = pd.read_csv(run_root / 'outputs/monthly_returns.csv', parse_dates=['date'])
    old = pd.read_csv(ROOT / 'snapshots/public-c8abb0f/monthly_returns.csv', parse_dates=['date'])
    joined = old[['date', 'VFS', 'Value', 'Market']].merge(monthly[['date', 'VFS', 'Value', 'Market']], on='date', suffixes=('_old', '_new'), validate='one_to_one')
    differences = {s: int((~np.isclose(joined[s + '_old'], joined[s + '_new'], rtol=0, atol=1e-12, equal_nan=True)).sum()) for s in ['VFS', 'Value', 'Market']}
    for name in ['monthly_returns.csv', 'performance_summary.csv', 'vfs_strategy_summary.csv', 'ff3_alphas.csv', 'paired_mean_test.csv', 'robustness.csv', 'input_snapshot.json', 'gate_a.json']:
        shutil.copyfile(run_root / 'outputs' / name, output / ('recollected_' + name))
    panel = pd.read_parquet(run_root / 'data/private/pit_panel.parquet')
    gaps = holdings_gaps(panel, workspace / 'data/private')
    gaps.to_csv(output / 'recollected_held_missing_monthly.csv', index=False)
    diagnose_held_gaps(workspace, ff3, output)
    import vfs_research.backtest as engine
    original_weights = engine.make_weights
    def neutral_weights(q, equal_weight=False):
        target, cells = original_weights(q, equal_weight)
        try:
            target['VFS'] = g_neutral_weights(q)
        except ValueError:
            target['VFS'] = None
        return target, cells
    try:
        engine.make_weights = neutral_weights
        from .data_ingest import load_benchmark
        neutral, _, _ = engine.run(panel, load_benchmark(ff3))
    finally:
        engine.make_weights = original_weights
    z = monthly[['date', 'VFS', 'rf']].merge(neutral[['date', 'VFS']].rename(columns={'VFS': 'GNeutral'}), on='date', validate='one_to_one')
    z['common_valid'] = z[['VFS', 'GNeutral']].notna().all(axis=1)
    dates = longest_block(z)
    z['comparison_window'] = z.date.isin(dates)
    z['spread'] = z.VFS - z.GNeutral
    z.to_csv(output / 'exploratory_g_neutral_monthly.csv', index=False)
    fac = load_factors(workspace).drop(columns='rf')
    q = z.loc[z.comparison_window].merge(fac, on='date', validate='one_to_one')
    stats = []
    for lag in [3, 6]:
        row = regression(q, 'spread', hac=lag)
        row['comparison'] = 'VFS_MINUS_PBR_BUDGET_MATCHED_G_NEUTRAL_EXPLORATORY'
        stats.append(row)
    pd.DataFrame(stats).to_csv(output / 'exploratory_g_neutral_alpha.csv', index=False)
    family = pd.concat([pd.read_csv(run_root / 'outputs/ff3_alphas.csv'), pd.DataFrame(stats)], ignore_index=True)
    family['p_holm'] = np.nan
    tested = family.p_hac.notna()
    if tested.any():
        from statsmodels.stats.multitest import multipletests
        family.loc[tested, 'p_holm'] = multipletests(family.loc[tested, 'p_hac'], method='holm')[1]
    family['role'] = 'EXPLORATORY_EIGHT_TEST_FAMILY_INDIVIDUAL_HAC_CI'
    family.to_csv(output / 'followup_multiplicity.csv', index=False)
    summary = {'status': 'RAW_SOURCE_VFS_REPLAY_COMPLETED', 'baseline_commit': 'c8abb0fd648df9eed6b80250cd25b96ca67963b2',
               'old_private_files_used': False, 'current_evidence': evidence,
               'old_joint_panel_sha256': old_evidence['source_panel_sha256'],
               'joint_panel_hash_equal': evidence['source_panel_sha256'] == old_evidence['source_panel_sha256'],
               'changed_monthly_returns_above_1e_12': differences,
               'economic_returns_repaired': 0, 'held_missing_records': int(gaps.missing_held_securities.sum()) if len(gaps) else 0,
               'g_neutral_common_contiguous_months': len(dates),
               'independent_oos': 'UNVERIFIED', 'source_redistribution': 'UNVERIFIED_NO_GITHUB_UPLOAD',
               'factor_source': 'PUBLISHED_LEGACY_FACTOR_AGGREGATES_CONDITIONAL_MODEL',
               'old_per_file_raw_responses_available': False,
               'isolated_run_name':run_name,
               'auxiliary_audit_compatibility_fix':'cost_regression_merges_factor_columns_without_replacing_primary_rf',
               'hash_difference_interpretation': 'current_receipts_and_serialization_are_recorded_no_old_hash_is_forced'}
    write_json(output / 'raw_replay_summary.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', required=True)
    parser.add_argument('--ff3-root', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--run-name',default='vfs-vintage-run')
    args = parser.parse_args()
    print(json.dumps(run(args.workspace, args.ff3_root, args.output,args.run_name), ensure_ascii=False))


if __name__ == '__main__':
    main()
