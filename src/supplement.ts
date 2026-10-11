import assert from 'node:assert/strict';
import { mkdirSync } from 'node:fs';
import { resolve, basename } from 'node:path';
import { spawnSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { root, json, csv, streamCsv, numeric, mean, median, variance, hash, streamHash, writeJson, writeCsv, outputDir, months } from './research_io.js';

export interface Member { stock_code: string; cohort: number; cell: string; pbr_group: string; lag_me: number; pbr: number; roe: number | null; }
interface Observation { stock_code: string; date: string; return: number | null; }
interface PanelExport { members: Member[]; observations: Observation[]; source_panel_hash: string; pit_validated: boolean; }
interface FnRecord { total: number | null; totalPrice: number | null; adjustedPrice: number | null; }
export interface Pair { good: Member; bad: Member; distance: number; }
export interface Plan { windows: Record<string, [string, string]>; matching: { max_abs_log_me_difference: number; max_abs_roe_difference: number; max_abs_log_pbr_difference: number }; }

function extractPanel(panelPath: string, cache: string): PanelExport {
  // Serialization adapter only: reuse the original validated formation functions.
  const code = `import sys,pandas as pd,json,hashlib
from vfs_research.core_hypotheses import validate_cell_input
from vfs_research.core_cross_section import annual_membership
from vfs_research.pit_features import validate_panel
p=validate_cell_input(pd.read_parquet(sys.argv[1])); validate_panel(p)
m=annual_membership(p)
v={'members':json.loads(m.to_json(orient='records',double_precision=15)), 'observations':json.loads(p[['stock_code','date','return']].to_json(orient='records',date_format='iso',double_precision=15)), 'source_panel_hash':hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest(), 'pit_validated':True}
open(sys.argv[2],'w',encoding='utf-8').write(json.dumps(v,allow_nan=False))`;
  const r = spawnSync(process.env.VFS_PYTHON ?? 'python', ['-c', code, panelPath, cache], { cwd: root, env: { ...process.env, PYTHONPATH: resolve(root, 'src') }, encoding: 'utf8' });
  if (r.status !== 0) throw new Error(r.stderr);
  return json<PanelExport>(cache);
}

export function matchMembers(members: Member[], plan: Plan): Pair[] {
  const pairs: Pair[] = [];
  for (const cohort of [...new Set(members.map(m => m.cohort))].sort()) for (const group of ['Low', 'High']) {
    const q = members.filter(m => m.cohort === cohort && m.pbr_group === group && m.roe !== null && Number.isFinite(m.roe));
    const edges: Pair[] = [];
    for (const good of q.filter(m => m.cell.endsWith('Good'))) for (const bad of q.filter(m => m.cell.endsWith('Bad'))) {
      const d = [Math.abs(Math.log(good.lag_me / bad.lag_me)) / plan.matching.max_abs_log_me_difference,
        Math.abs(good.roe! - bad.roe!) / plan.matching.max_abs_roe_difference,
        Math.abs(Math.log(good.pbr / bad.pbr)) / plan.matching.max_abs_log_pbr_difference];
      if (d.every(v => v <= 1 + 1e-12)) edges.push({ good, bad, distance: d.reduce((a, v) => a + v ** 2, 0) });
    }
    edges.sort((a, b) => a.distance - b.distance || a.good.stock_code.localeCompare(b.good.stock_code) || a.bad.stock_code.localeCompare(b.bad.stock_code));
    const used = new Set<string>();
    for (const edge of edges) if (!used.has(edge.good.stock_code) && !used.has(edge.bad.stock_code)) {
      pairs.push(edge); used.add(edge.good.stock_code); used.add(edge.bad.stock_code);
    }
  }
  return pairs;
}

export function cappedWeights(members: Member[], equal = false, cap = .25): Map<string, number> {
  assert(members.length * cap >= 1 - 1e-12, 'infeasible cap');
  const w = new Map<string, number>(); let free = [...members];
  while (free.length) {
    const remaining = 1 - [...w.values()].reduce((a, b) => a + b, 0);
    const sum = free.reduce((a, m) => a + (equal ? 1 : m.lag_me), 0);
    const hit = free.filter(m => remaining * (equal ? 1 : m.lag_me) / sum > cap + 1e-12);
    if (!hit.length) { for (const m of free) w.set(m.stock_code, remaining * (equal ? 1 : m.lag_me) / sum); break; }
    for (const m of hit) w.set(m.stock_code, cap);
    free = free.filter(m => !w.has(m.stock_code));
  }
  assert(Math.abs([...w.values()].reduce((a, b) => a + b, 0) - 1) < 1e-12); return w;
}

export function weightedMoment(weights: Map<string, number>, values: Map<string, number | null>): { coverage: number; matched_n: number; missing_n: number; conditional: number | null; full: number | null } {
  let coverage = 0, contribution = 0, matched = 0;
  for (const [code, w] of weights) { const r = values.get(code); if (r !== null && r !== undefined && Number.isFinite(r) && r >= -1) { coverage += w; contribution += w * r; matched++; } }
  return { coverage, matched_n: matched, missing_n: weights.size - matched, conditional: coverage > 0 ? contribution / coverage : null, full: matched === weights.size ? contribution : null };
}
function drift(w: Map<string, number>, r: Map<string, number | null>): Map<string, number> {
  const m = weightedMoment(w, r); assert(m.full !== null && m.full > -1, 'missing/invalid/exhausted portfolio');
  return new Map([...w].map(([c, v]) => [c, v * (1 + r.get(c)!) / (1 + m.full!)]));
}

export async function analyze(): Promise<void> {
  const out = outputDir(); const workspace = resolve(root, '..');
  const privateDir = resolve(root, '_workspace/supplement'); mkdirSync(privateDir, { recursive: true });
  const dataDir = resolve(process.env.VFS_FNGUIDE_ROOT ?? resolve(workspace, 'fnguidedata'));
  const panelPath = resolve(process.env.VFS_PIT_PANEL ?? resolve(workspace, '04_이번작업_검증자료/verified_loaded_panel.parquet'));
  const plan = json<Plan>(resolve(root, 'config/supplement_plan.json'));
  const p = extractPanel(panelPath, resolve(privateDir, 'panel.json'));
  const prices = new Map(p.observations.map(r => [r.stock_code + '|' + r.date.slice(0, 7), r.return]));
  const fn = new Map<string, FnRecord>();
  const monthlyFile = resolve(dataDir, 'FnGuide_월간연간_종목데이터.csv');
  let totalRows = 0, annualRows = 0, monthlyRows = 0, totalValid = 0, invalidReturns = 0, duplicates = 0;
  let first = '9999', last = '0000', firstTotal = '9999', lastTotal = '0000'; const allCodes = new Set<string>(); let columns: string[] = [];
  for await (const r of streamCsv(monthlyFile)) {
    totalRows++; if (!columns.length) columns = Object.keys(r);
    if (r.frequency === 'annual') { annualRows++; continue; }
    assert(r.frequency === 'monthly', 'unknown frequency'); monthlyRows++;
    assert(/^A[A-Z0-9]{6}$/.test(r.code!), 'code convention'); assert(/^\d{4}-\d{2}$/.test(r.period!), 'month convention');
    first = r.period! < first ? r.period! : first; last = r.period! > last ? r.period! : last; allCodes.add(r.code!);
    const total = numeric(r.KR_return_cash_dividend_included_pct); if (total !== null) { totalValid++; firstTotal = r.period! < firstTotal ? r.period! : firstTotal; lastTotal = r.period! > lastTotal ? r.period! : lastTotal; }
    if (total !== null && total < -100) invalidReturns++;
    const key = r.code!.slice(1) + '|' + r.period!;
    if (fn.has(key)) duplicates++;
    fn.set(key, { total: total !== null && total >= -100 ? total / 100 : null, totalPrice: numeric(r.KR_price_cash_dividend_included_krw), adjustedPrice: numeric(r.S410000700__수정주가_원__일간) });
  }
  assert(duplicates === 0, 'ambiguous FnGuide security-month'); assert(columns.includes('KR_return_cash_dividend_included_pct'));
  const factorFile = resolve(dataDir, 'FnGuide_팩터금리_포트폴리오.csv'); const factors = csv(factorFile);
  const ratioDifferences: number[] = [];
  for (const [key, v] of fn) if (v.total !== null && v.totalPrice !== null) {
    const [code, month] = key.split('|'); const d = new Date(month! + '-01T00:00:00Z'); d.setUTCMonth(d.getUTCMonth() - 1);
    const prev = fn.get(code + '|' + d.toISOString().slice(0, 7));
    if (prev?.totalPrice && prev.totalPrice > 0) ratioDifferences.push(Math.abs(v.total - (v.totalPrice / prev.totalPrice - 1)));
  }
  writeJson(resolve(out, 'source_schema.json'), {
    files: [{ file: basename(monthlyFile), sha256: await streamHash(monthlyFile), total_rows: totalRows, monthly_rows: monthlyRows, annual_rows: annualRows, first_month: first, last_month: last, securities: allCodes.size, valid_dividend_returns: totalValid, first_valid_dividend_month: firstTotal, last_valid_dividend_month: lastTotal, invalid_below_minus100: invalidReturns, duplicate_security_months: duplicates, columns },
      { file: basename(factorFile), sha256: hash(factorFile), rows: factors.length, first_month: factors[0]!.period, last_month: factors.at(-1)!.period, columns: Object.keys(factors[0]!), role: 'SCHEMA_ONLY_NO_FACTOR_RESULTS_USED' }],
    return_unit: 'percent / 100 = decimal', me_unit: 'original PIT lag_me: thousand KRW; table billion KRW = lag_me / 1e6', roe_unit: 'original PIT decimal; percentage = roe * 100',
    dividend_price_ratio_check: { comparisons: ratioDifferences.length, max_abs_decimal_error: ratioDifferences.reduce((a, b) => Math.max(a, b), 0), above_1bp: ratioDifferences.filter(v => v > .0001).length },
    new_financials_used_for_selection_or_controls: false, factor_results_used: false, economic_payoff_verified: false,
    private_panel_sha256: p.source_panel_hash, pit_validated: p.pit_validated, plan_sha256: hash(resolve(root, 'config/supplement_plan.json'))
  });

  const dividendRows: Record<string, string | number | boolean | null>[] = [];
  const weightsPrivate: Record<string, unknown>[] = [];
  for (const group of ['Low', 'High', 'Strategy']) for (const weighting of ['VW', 'EW']) {
    const [start, end] = plan.windows[group]!; const members = p.members.filter(m => m.cohort === Number(start.slice(0, 4)));
    const legs = group === 'Strategy' ? ['VFS', 'Value'] : [group + '-Good', group + '-Bad'];
    for (const leg of legs) {
      let original: Map<string, number>;
      if (leg === 'VFS') original = new Map(['Low-Good', 'High-Good'].flatMap(cell => [...cappedWeights(members.filter(m => m.cell === cell), weighting === 'EW')].map(([c, w]): [string, number] => [c, w * .5])));
      else if (leg === 'Value') { const low = members.filter(m => m.pbr_group === 'Low'); const sum = low.reduce((a, m) => a + (weighting === 'EW' ? 1 : m.lag_me), 0); original = new Map(low.map(m => [m.stock_code, (weighting === 'EW' ? 1 : m.lag_me) / sum])); }
      else original = cappedWeights(members.filter(m => m.cell === leg), weighting === 'EW');
      let totalDrift: Map<string, number> | null = new Map(original);
      for (const month of months(start, end)) {
        const price = new Map([...original.keys()].map(c => [c, prices.get(c + '|' + month) ?? null]));
        const total = new Map([...original.keys()].map(c => [c, fn.get(c + '|' + month)?.total ?? null]));
        const priceOnTotal = new Map([...original.keys()].map(c => [c, total.get(c) !== null ? price.get(c)! : null]));
        const prior = new Date(month + '-01T00:00:00Z'); prior.setUTCMonth(prior.getUTCMonth() - 1);
        const fnAdjusted = new Map([...original.keys()].map(c => {
          const current = fn.get(c + '|' + month)?.adjustedPrice; const previous = fn.get(c + '|' + prior.toISOString().slice(0, 7))?.adjustedPrice;
          return [c, total.get(c) !== null && current !== null && current !== undefined && previous && previous > 0 ? current / previous - 1 : null] as [string, number | null];
        }));
        const a = weightedMoment(original, price); const b = weightedMoment(original, total); const matched = weightedMoment(original, priceOnTotal);
        assert(a.full !== null, 'original locked window does not replay');
        assert(b.conditional !== null && matched.conditional !== null, 'no comparable dividend-matched observations; cannot substitute zero');
        const self: ReturnType<typeof weightedMoment> | null = totalDrift ? weightedMoment(totalDrift, total) : null;
        dividendRows.push({ group, weighting, leg, month, held_n: original.size, original_price_return: a.full, matched_price_conditional: matched.conditional,
          total_fixed_weights_conditional: b.conditional, total_fixed_weights_complete: b.full, matched_n: b.matched_n, missing_n: b.missing_n, original_weight_coverage: b.coverage,
          fn_adjusted_price_weight_coverage: weightedMoment(original, fnAdjusted).coverage, fn_adjusted_price_conditional: weightedMoment(original, fnAdjusted).conditional,
          total_self_financing_complete: self?.full ?? null, status: b.full !== null ? 'COMPLETE_RETURN_FIELD_MATCH_FROZEN_PRICE_WEIGHTS' : 'PARTIAL_MATCH_CONDITIONAL_MOMENT_NOT_NAV' });
        weightsPrivate.push({ group, weighting, leg, month, weights: Object.fromEntries(original) });
        original = drift(original, price);
        totalDrift = self?.full !== null && self?.full !== undefined && totalDrift ? drift(totalDrift, total) : null;
      }
    }
  }
  writeJson(resolve(privateDir, 'weight_replay.json'), weightsPrivate);
  writeCsv(resolve(out, 'dividend_monthly.csv'), dividendRows);
  const dividendSummary: Record<string, string | number | boolean | null>[] = [];
  for (const group of ['Low', 'High', 'Strategy']) for (const weighting of ['VW', 'EW']) {
    const a = dividendRows.filter(r => r.group === group && r.weighting === weighting); const legNames = [...new Set(a.map(r => String(r.leg)))];
    const good = a.filter(r => r.leg === legNames[0]); const bad = a.filter(r => r.leg === legNames[1]);
    const spread = (key: string): number => mean(good.map((r, i) => Number(r[key]) - Number(bad[i]![key]))) * 100;
    const complete = a.every(r => r.total_fixed_weights_complete !== null);
    const selfComplete = a.every(r => r.total_self_financing_complete !== null);
    const cum = (q: typeof a, key: string): number => (q.reduce((v, r) => v * (1 + Number(r[key])), 1) - 1) * 100;
    dividendSummary.push({ group, weighting, start: plan.windows[group]![0], end: plan.windows[group]![1], months: good.length,
      original_price_spread_pp: spread('original_price_return'), matched_price_spread_pp: spread('matched_price_conditional'), dividend_conditional_spread_pp: spread('total_fixed_weights_conditional'),
      dividend_complete_spread_pp: complete ? spread('total_fixed_weights_complete') : null, self_financing_spread_pp: selfComplete ? spread('total_self_financing_complete') : null,
      good_price_cumulative_pct: cum(good, 'original_price_return'), bad_price_cumulative_pct: cum(bad, 'original_price_return'),
      good_total_fixed_weights_cumulative_pct: complete ? cum(good, 'total_fixed_weights_complete') : null, bad_total_fixed_weights_cumulative_pct: complete ? cum(bad, 'total_fixed_weights_complete') : null,
      good_self_financing_cumulative_pct: selfComplete ? cum(good, 'total_self_financing_complete') : null, bad_self_financing_cumulative_pct: selfComplete ? cum(bad, 'total_self_financing_complete') : null,
      min_weight_coverage: Math.min(...a.map(r => Number(r.original_weight_coverage))), expected_security_months: a.reduce((v, r) => v + Number(r.held_n), 0), matched_security_months: a.reduce((v, r) => v + Number(r.matched_n), 0),
      complete_return_field_match: complete, economic_payoff_verified: false });
  }
  writeCsv(resolve(out, 'dividend_summary.csv'), dividendSummary);

  const pairs = matchMembers(p.members, plan); writeJson(resolve(privateDir, 'matched_pairs.json'), pairs);
  const balance: Record<string, string | number | boolean | null>[] = [];
  for (const cohort of [...new Set(p.members.map(m => m.cohort))]) for (const group of ['Low', 'High']) {
    const eligible = p.members.filter(m => m.cohort === cohort && m.pbr_group === group && m.roe !== null);
    const matched = pairs.filter(q => q.good.cohort === cohort && q.good.pbr_group === group);
    for (const feature of ['log_me', 'roe', 'log_pbr']) {
      const value = (m: Member): number => feature === 'log_me' ? Math.log(m.lag_me) : feature === 'log_pbr' ? Math.log(m.pbr) : m.roe!;
      const g0 = eligible.filter(m => m.cell.endsWith('Good')).map(value), b0 = eligible.filter(m => m.cell.endsWith('Bad')).map(value);
      const sd = Math.sqrt((variance(g0) + variance(b0)) / 2);
      const g1 = matched.map(q => value(q.good)), b1 = matched.map(q => value(q.bad));
      assert(Number.isFinite(sd) && sd > 0 && matched.length > 1, 'balance unavailable: insufficient matching support');
      balance.push({ cohort, group, feature, eligible_good_n: g0.length, eligible_bad_n: b0.length, matched_pairs: matched.length,
        before_good_mean: mean(g0), before_bad_mean: mean(b0), after_good_mean: mean(g1), after_bad_mean: mean(b1),
        before_smd: (mean(g0) - mean(b0)) / sd, after_smd_original_sd: (mean(g1) - mean(b1)) / sd,
        before_good_median: median(g0), before_bad_median: median(b0), after_good_median: median(g1), after_bad_median: median(b1) });
    }
  }
  writeCsv(resolve(out, 'matching_balance.csv'), balance);
  const matchedMonthly: Record<string, string | number | boolean | null>[] = [];
  for (const group of ['Low', 'High']) for (const month of months('2021-07', '2026-04')) {
    const cohort = Number(month.slice(0, 4)) - (Number(month.slice(5)) < 7 ? 1 : 0);
    const all = p.members.filter(m => m.cohort === cohort && m.pbr_group === group); const eligible = all.filter(m => m.roe !== null);
    const valid = (r: number | null | undefined): r is number => r !== null && r !== undefined && Number.isFinite(r) && r >= -1;
    const ret = (m: Member): number | null | undefined => prices.get(m.stock_code + '|' + month);
    const g = eligible.filter(m => m.cell.endsWith('Good')).map(ret).filter(valid), b = eligible.filter(m => m.cell.endsWith('Bad')).map(ret).filter(valid);
    const q = pairs.filter(x => x.good.cohort === cohort && x.good.pbr_group === group);
    const observed = q.filter(x => valid(ret(x.good)) && valid(ret(x.bad)));
    const dual = observed.filter(x => valid(fn.get(x.good.stock_code + '|' + month)?.total) && valid(fn.get(x.bad.stock_code + '|' + month)?.total));
    assert(g.length && b.length && observed.length && dual.length, 'empty observed comparison; do not publish missing as zero');
    matchedMonthly.push({ group, month, cohort, original_formation_n: all.length, pit_roe_eligible_n: eligible.length,
      eligible_good_observed_n: g.length, eligible_bad_observed_n: b.length, matched_formation_pairs: q.length, observed_pairs: observed.length, missing_pairs: q.length - observed.length,
      before_price_spread: mean(g) - mean(b), matched_price_spread: mean(observed.map(x => ret(x.good)! - ret(x.bad)!)),
      dual_observed_pairs: dual.length, dual_price_spread: mean(dual.map(x => ret(x.good)! - ret(x.bad)!)), matched_total_spread: mean(dual.map(x => fn.get(x.good.stock_code + '|' + month)!.total! - fn.get(x.bad.stock_code + '|' + month)!.total!)),
      role: 'OBSERVED_PAIR_MOMENT_NOT_INVESTABLE_NAV_NO_CAUSAL_INFERENCE' });
  }
  writeCsv(resolve(out, 'matching_monthly.csv'), matchedMonthly);
  const matchingSummary = ['Low', 'High'].map(group => {
    const a = matchedMonthly.filter(r => r.group === group); const b = balance.filter(r => r.group === group);
    return { group, months: a.length, formation_cohorts: 5, total_formation_pairs: pairs.filter(x => x.good.pbr_group === group).length,
      before_price_spread_pp: mean(a.map(r => Number(r.before_price_spread))) * 100, matched_price_spread_pp: mean(a.map(r => Number(r.matched_price_spread))) * 100,
      dual_price_spread_pp: mean(a.map(r => Number(r.dual_price_spread))) * 100, matched_total_spread_pp: mean(a.map(r => Number(r.matched_total_spread))) * 100,
      expected_pair_months: a.reduce((v, r) => v + Number(r.matched_formation_pairs), 0), observed_pair_months: a.reduce((v, r) => v + Number(r.observed_pairs), 0),
      dual_observed_pair_months: a.reduce((v, r) => v + Number(r.dual_observed_pairs), 0),
      max_abs_post_smd: Math.max(...b.map(r => Math.abs(Number(r.after_smd_original_sd)))), inference: 'NOT_ESTIMATED_5_COHORTS_EXPLORATORY',
      comparison: 'Same months and PIT-ROE eligibility; different membership after matching, pairwise deletion only for moments' };
  });
  writeJson(resolve(out, 'matching_summary.json'), matchingSummary);
  writeJson(resolve(out, 'summary.json'), { question: '거버넌스는 PBR에 추가적인 투자 정보를 제공하는가?', plan_sha256: hash(resolve(root, 'config/supplement_plan.json')), baseline_modified: false, dividend: dividendSummary, matching: matchingSummary });
  console.log(JSON.stringify({ dividend: dividendSummary, matching: matchingSummary }, null, 2));
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) await analyze();
