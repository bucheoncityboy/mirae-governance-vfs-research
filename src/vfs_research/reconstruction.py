"""Public-source continuation without old PC paths or modified legacy files."""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import sys
import zipfile
import io
import xml.etree.ElementTree as ET
import urllib.request

import numpy as np
import pandas as pd

from .data_ingest import ROOT, digest
from .portfolio import capped_weights
from .stats import performance
from .strategy_diagnostics import vfs_observed_window


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def legacy_modules(workspace, ff3):
    """Bind archived functions to new local roots; archive bytes stay unchanged."""
    workspace, ff3 = Path(workspace).resolve(), Path(ff3).resolve()
    if workspace == ROOT or ROOT in workspace.parents or workspace == ff3 or ff3 in workspace.parents:
        raise ValueError('collection workspace must be outside both repositories')
    for rel in ['config', 'data/private', 'data/raw', 'output']:
        (workspace / rel).mkdir(parents=True, exist_ok=True, mode=0o700)
    archive = ROOT / 'legacy_governance_pilot'
    for name in ['pre_registration.yaml', 'pre_registration.lock.json']:
        target = workspace / 'config' / name
        source = archive / 'config' / name
        if target.exists() and digest(target) != digest(source):
            raise ValueError('copied legacy design lock changed')
        if not target.exists():
            shutil.copyfile(source, target)
    sys.path.insert(0, str(ROOT))
    acquire = importlib.import_module('legacy_governance_pilot.src.acquire')
    acquire.Client = importlib.import_module('legacy_governance_pilot.src.dart_client').Client
    acquire.ROOT, acquire.SOURCE = workspace, ff3
    build = importlib.import_module('legacy_governance_pilot.src.build_governance_panel')
    build.ROOT, build.SOURCE = workspace, ff3
    acquire.verify_registration()
    return acquire, build


def official_api_opener(url, timeout):
    request = urllib.request.Request(url, headers={
        'Accept': 'application/json,application/zip',
        'User-Agent': 'VFSResearch/1.0 (official OpenDART API client)'})
    return urllib.request.urlopen(request, timeout=timeout)


def prepare(workspace, ff3):
    acquire, _ = legacy_modules(workspace, ff3)
    p = acquire.panel()
    u = p.groupby('stock_code').agg(name=('name', 'first'), first_month=('date', 'min'),
                                  last_month=('date', 'max'), stock_months=('date', 'size'),
                                  valid_returns=('return', 'count'))
    size = p.loc[p.date.eq('2014-12-01'), ['stock_code', 'me']].set_index('stock_code').me
    u['predefined_ME_2014_12'] = size
    strata = ((size.rank(method='first') - 1) * 3 / len(size)).astype(int)
    groups = [list(strata.loc[strata.eq(i)].index.sort_values()) for i in range(3)]
    order = [group[i] for i in range(max(map(len, groups))) for group in groups if i < len(group)]
    order += sorted(set(u.index) - set(order))
    ranks = {code: i for i, code in enumerate(order)}
    u['acquisition_order'] = [ranks[code] for code in u.index]
    u.to_csv(Path(workspace) / 'data/private/universe.csv')
    book = pd.read_parquet(Path(ff3) / 'data/book_equity_monthly.parquet')
    book.sort_values('date').groupby(['code', 'be_year']).first().reset_index().to_parquet(
        Path(workspace) / 'data/private/fiscal_book.parquet', index=False)
    jobs = 0
    cfg = acquire.verify_registration()
    for row in u.itertuples():
        for year in cfg['years']:
            jobs += row.last_month >= pd.Timestamp(year=year + 1, month=1, day=1) and row.first_month <= pd.Timestamp(year=year + 1, month=12, day=1)
    result = {'status': 'LOCAL_BASELINE_PREPARED', 'source_companies': len(u),
              'source_stock_months': len(p), 'planned_annual_company_year_jobs': int(jobs),
              'minimum_pair_requests_before_mapping_or_retries': int(2 * jobs),
              'per_run_budget': 19000, 'full_collection_gate': 'AUTHENTICATED_SMOKE_REQUIRED',
              'historical_mapping': 'GLOBAL_ANNUAL_FILINGS_REQUIRED_CURRENT_CORPCODE_ALONE_INSUFFICIENT',
              'market_classification': 'DO_NOT_USE_TICKER_DIGITS', 'raw_redistribution': 'UNVERIFIED_DO_NOT_UPLOAD'}
    write_json(Path(workspace) / 'baseline_status.json', result)
    return result


def configure_key(file):
    if file:
        path = Path(file).resolve()
        if path == ROOT or ROOT in path.parents or path.stat().st_mode & 0o077:
            raise ValueError('credential must be private and outside the repository')
        value = path.read_text().strip()
        if len(value) != 40 or not value.isalnum():
            raise ValueError('invalid credential format')
        os.environ['DART_API_KEY'] = value


def smoke(workspace, ff3, key_file=None, budget=200):
    if not 1 <= budget <= 200:
        raise ValueError('smoke budget must be between 1 and 200')
    prepare(workspace, ff3)
    configure_key(key_file)
    acquire, _ = legacy_modules(workspace, ff3)
    client = acquire.Client(Path(workspace) / 'data', budget=budget, interval=.3, opener=official_api_opener)
    # Share one counted budget across nested/parallel legacy collection functions.
    acquire.Client = lambda *args, **kwargs: client
    result = {'status': 'PENDING', 'role': 'RAW_RECOLLECTION_SMOKE_NOT_PORTFOLIO_BACKTEST',
              'request_budget': budget, 'new_requests': 0, 'verified_governance_rows': 0,
              'verified_financial_rows': 0, 'retrieved_vintage': 'CURRENT_RESPONSE_ORIGINAL_BEFORE_CORRECTION_UNVERIFIED'}
    try:
        # The archived collector already supports official historical list.json
        # mapping, which also retains early exits. corpCode.xml is not a gate
        # when its ZIP route is unavailable but authenticated JSON routes work.
        acquire.mapping(smoke_only=True)
        mapping = pd.read_csv(Path(workspace) / 'data/private/ticker_map.csv',
                              dtype={'stock_code': str, 'corp_code': str})
        cfg = acquire.verify_registration()
        chosen = mapping.loc[mapping.stock_code.isin(cfg['smoke_codes']) & mapping.corp_codes_per_ticker.eq(1)]
        if len(chosen) != len(cfg['smoke_codes']):
            raise acquire.APIError('smoke_historical_mapping_missing_or_ambiguous')
        records = pd.read_parquet(Path(workspace) / 'data/private/annual_filings.parquet').to_dict('records')
        for row in chosen.itertuples():
            filings, hashes = client.filings(row.corp_code)
            records += [{**f, 'filing_list_hash': '|'.join(hashes)} for f in filings]
        pd.DataFrame(records).drop_duplicates(['corp_code', 'rcept_no']).to_parquet(
            Path(workspace) / 'data/private/annual_filings.parquet', index=False)
        acquire.fetch('smoke')
        from legacy_governance_pilot.src.verify_evidence import verify_g_frame, verify_financial_frame
        g = verify_g_frame(pd.read_parquet(Path(workspace) / 'data/private/governance_observations.parquet'), Path(workspace) / 'data/raw')
        f = verify_financial_frame(pd.read_parquet(Path(workspace) / 'data/private/verified_financials.parquet'), Path(workspace) / 'data/raw')
        result.update(verified_governance_rows=int(g.raw_verified.sum()), verified_financial_rows=len(f),
                      status='PASS_PARTIAL_COVERAGE' if g.raw_verified.any() and len(f) else 'FAIL_NO_VERIFIED_JOINT_EVIDENCE')
    except acquire.APIError as error:
        result.update(status='BLOCKED', reason=str(error))
    result['new_requests'] = client.count
    write_json(Path(workspace) / 'smoke_status.json', result)
    return result


def collect(workspace, ff3, key_file=None, budget=19000, stage='50'):
    gate = json.loads((Path(workspace) / 'smoke_status.json').read_text())
    if gate['status'] != 'PASS_PARTIAL_COVERAGE':
        raise ValueError('collection refused: authenticated evidence smoke did not pass')
    if not 1 <= budget <= 19000 or stage not in ['50', '150', 'all']:
        raise ValueError('invalid collection stage/budget')
    configure_key(key_file)
    acquire, _ = legacy_modules(workspace, ff3)
    # Official historical filing lists resolve early exits and ambiguous ticker mappings.
    # Preserve the archived client's 0.15-second throttle; cached responses are
    # reused by verified digest. The request budget remains independently capped.
    client = acquire.Client(Path(workspace) / 'data', budget=budget, interval=.15, opener=official_api_opener)
    acquire.Client = lambda *args, **kwargs: client
    acquire.mapping()
    acquire.fetch(stage)
    return json.loads((Path(workspace) / 'output/acquisition_status.json').read_text())


def build(workspace, ff3):
    _, builder = legacy_modules(workspace, ff3)
    builder.build()
    return json.loads((Path(workspace) / 'output/pit_status.json').read_text())


def g_neutral_weights(classified):
    """Exploratory 50:50 PBR-budget comparator; no G selection or outcome tuning."""
    weights = []
    for group in ['Low', 'High']:
        leg = classified.loc[classified.pbr_group.eq(group)].set_index('stock_code').lag_me
        weights.append(.5 * capped_weights(leg))
    return pd.concat(weights)


def public_audit(ff3, output, private):
    """Recompute published aggregates and audit prices, without claiming raw VFS replay."""
    ff3, output, private = Path(ff3), Path(output), Path(private)
    output.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True, mode=0o700)
    d = pd.read_csv(ROOT / 'outputs/monthly_returns.csv', parse_dates=['date'])
    paired = d.loc[d.primary_window]
    own = vfs_observed_window(d)
    result = {'status': 'PASS', 'scope': 'PUBLISHED_AGGREGATE_ARITHMETIC_ONLY',
              'raw_vfs_rebuilt': False, 'paired_months': len(paired), 'vfs_own_months': len(own),
              'paired': [performance(paired, s) for s in ['VFS', 'Value', 'Market']],
              'vfs_own': [performance(own, s) for s in ['VFS', 'Market']],
              'mean_monthly_spread_percentage_points': float(paired.spread.mean() * 100),
              'alpha_status': 'NOT_ESTIMATED'}
    for name, calculated in [('performance_summary.csv', result['paired']), ('vfs_strategy_summary.csv', result['vfs_own'])]:
        expected = pd.read_csv(ROOT / 'outputs' / name).set_index('strategy')
        for row in calculated:
            for col in ['total_return', 'cagr', 'volatility', 'sharpe', 'sortino', 'mdd']:
                if not np.isclose(row[col], expected.loc[row['strategy'], col], rtol=0, atol=1e-12):
                    raise ValueError('published arithmetic mismatch')
    write_json(output / 'published_arithmetic.json', result)
    inventory = []
    for path in sorted((ff3 / 'data').glob('*.parquet')):
        frame = pd.read_parquet(path)
        inventory.append({'file': path.name, 'sha256': digest(path), 'bytes': path.stat().st_size,
                          'rows': len(frame), 'columns': list(frame), 'start': str(frame.date.min()),
                          'end': str(frame.date.max()), 'redistribution': 'UNVERIFIED_NO_NEW_UPLOAD'})
    write_json(output / 'ff3_input_inventory.json', {'files': inventory, 'source_role': 'OWNER_AUTHORIZED_LOCAL_ANALYSIS_NOT_OPEN_DATA_LICENSE'})
    raw = pd.read_parquet(ff3 / 'data/market_data_long.parquet')
    price = raw.loc[raw.item_code.eq('S410000700'), ['code', 'date', 'value']].sort_values(['code', 'date'])
    price['unfiltered'] = price.groupby('code').value.pct_change(fill_method=None)
    z = pd.read_parquet(ff3 / 'data/stock_returns.parquet').merge(price, on=['code', 'date'], validate='one_to_one')
    z['gt100_filtered'] = z.unfiltered.abs().gt(1) & z['return'].isna()
    z['missing_return'] = z['return'].isna()
    z['first_price'] = z.groupby('code').cumcount().eq(0)
    z['price_unavailable'] = z.value.isna()
    z['previous_price_unavailable'] = z.groupby('code').value.shift(1).isna() & ~z.first_price
    z.to_parquet(private / 'price_audit.parquet', index=False)
    z.groupby('date').agg(gt100_filtered=('gt100_filtered', 'sum'), missing_returns=('missing_return', 'sum'),
                         first_price=('first_price', 'sum'), price_unavailable=('price_unavailable', 'sum'),
                         previous_price_unavailable=('previous_price_unavailable', 'sum')).to_csv(output / 'price_filter_monthly.csv')
    finite = z['return'].notna() & z.unfiltered.notna()
    events = {'gt100_filtered': int(z.gt100_filtered.sum()), 'missing_returns': int(z.missing_return.sum()),
              'price_arithmetic_max_abs_error': float((z.loc[finite, 'return'] - z.loc[finite, 'unfiltered']).abs().max()),
              'economic_returns_corrected': 0, 'official_corporate_action_verification': 'UNVERIFIED',
              'original_ff3_inputs_modified': False,
              'held_security_attribution': 'BLOCKED_MISSING_JOINT_G_PIT_PANEL',
              'missingness_categories_overlap': True}
    write_json(output / 'return_audit_summary.json', events)
    reasons = []
    for s in ['VFS', 'Value']:
        for reason, group in d.groupby(s + '_reason'):
            reasons.append({'strategy': s, 'reason': reason, 'months': len(group),
                            'first_month': str(group.date.min().date()), 'last_month': str(group.date.max().date()),
                            'role': 'PUBLISHED_PATH_DIAGNOSTIC_NOT_HOLDINGS_RECONSTRUCTION'})
    pd.DataFrame(reasons).to_csv(output / 'published_missing_path_reasons.csv', index=False)
    return {**events, 'published_arithmetic': 'PASS', 'paired_months': len(paired), 'own_months': len(own)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['prepare', 'public-audit', 'smoke', 'collect', 'build'])
    parser.add_argument('--ff3-root', required=True)
    parser.add_argument('--workspace', required=True)
    parser.add_argument('--output', default=str(ROOT / 'outputs/reconstruction'))
    parser.add_argument('--key-file')
    parser.add_argument('--budget', type=int)
    parser.add_argument('--stage', default='50')
    args = parser.parse_args()
    if args.command == 'public-audit':
        result = public_audit(args.ff3_root, args.output, args.workspace)
    elif args.command == 'smoke':
        result = smoke(args.workspace, args.ff3_root, args.key_file, args.budget or 200)
    elif args.command == 'collect':
        result = collect(args.workspace, args.ff3_root, args.key_file, args.budget or 19000, args.stage)
    elif args.command == 'build':
        result = build(args.workspace, args.ff3_root)
    else:
        result = prepare(args.workspace, args.ff3_root)
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


if __name__ == '__main__':
    main()
