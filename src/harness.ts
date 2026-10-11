import assert from 'node:assert/strict';
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { root, json, csv, mean, hash, numeric, writeJson, months } from './research_io.js';
import { matchMembers, weightedMoment, cappedWeights, type Member, type Plan, type Pair } from './supplement.js';

const out = resolve(root, 'outputs/supplement');
const close = (a: number | null, b: number | null, tol = 1e-12): void => { assert(a !== null && b !== null && Number.isFinite(a) && Number.isFinite(b)); assert(Math.abs(a - b) < tol, `${a} != ${b}`); };
const normalizedHash = (buffer: Buffer): string => createHash('sha256').update(buffer.toString('utf8').replaceAll('\r\n', '\n')).digest('hex');
if (process.argv.includes('--capture-baseline')) {
  const ref = execFileSync('git', ['rev-parse', 'origin/main'], { cwd: root, encoding: 'utf8' }).trim();
  const listed = execFileSync('git', ['ls-tree', '-r', '--name-only', ref], { cwd: root, encoding: 'utf8' }).trim().split('\n');
  const selected = listed.filter(f => f.startsWith('outputs/core_hypotheses/') && /\.(csv|json)$/.test(f) || ['outputs/monthly_returns.csv', 'outputs/robustness.csv', 'config/vfs_pre_analysis_plan.yaml', 'config/design_lock.json', 'config/core_hypotheses_exploratory_plan.yaml', 'src/vfs_research/core_hypotheses.py', 'src/vfs_research/core_cross_section.py', 'src/vfs_research/backtest.py', 'src/vfs_research/portfolio.py'].includes(f));
  const files = Object.fromEntries(selected.map(f => [f, normalizedHash(execFileSync('git', ['show', ref + ':' + f], { cwd: root }))]));
  writeJson(resolve(root, 'docs/supplement_baseline_hashes.json'), { baseline: ref, normalization: 'UTF8_CRLF_TO_LF', files });
}
const protectedFiles = json<{ files: Record<string, string> }>(resolve(root, 'docs/supplement_baseline_hashes.json'));
for (const [f, sha] of Object.entries(protectedFiles.files)) assert.equal(normalizedHash(readFileSync(resolve(root, f))), sha, 'Original evidence changed: ' + f);
const locked = json<{ files: Record<string, string> }>(resolve(root, 'docs/core_baseline_hashes.json'));
for (const [f, sha] of Object.entries(locked.files)) assert.equal(hash(resolve(root, f)), sha, 'Locked historical evidence changed: ' + f);

const plan = json<Plan>(resolve(root, 'config/supplement_plan.json'));
const source = json<{ plan_sha256: string; pit_validated: boolean; new_financials_used_for_selection_or_controls: boolean; factor_results_used: boolean; dividend_price_ratio_check: { comparisons: number; max_abs_decimal_error: number }; files: { duplicate_security_months?: number }[] }>(resolve(out, 'source_schema.json'));
assert.equal(source.plan_sha256, hash(resolve(root, 'config/supplement_plan.json'))); assert(source.pit_validated); assert.equal(source.new_financials_used_for_selection_or_controls, false); assert.equal(source.factor_results_used, false);
assert.equal(source.files[0]!.duplicate_security_months, 0); assert(source.dividend_price_ratio_check.max_abs_decimal_error < 1e-12);
const dividend = csv(resolve(out, 'dividend_monthly.csv')); const dividendSummary = csv(resolve(out, 'dividend_summary.csv'));
for (const r of dividend) {
  assert(Number(r.matched_n) + Number(r.missing_n) === Number(r.held_n)); assert(Number(r.original_weight_coverage) > 0 && Number(r.original_weight_coverage) <= 1 + 1e-12);
  if (Number(r.missing_n)) assert.equal(r.total_fixed_weights_complete, '', 'Partial match must not masquerade as portfolio return');
  else close(numeric(r.total_fixed_weights_complete), numeric(r.total_fixed_weights_conditional));
}
const cells = csv(resolve(root, 'outputs/core_hypotheses/cell_monthly_returns.csv')); const strategies = csv(resolve(root, 'outputs/monthly_returns.csv'));
for (const r of dividend.filter(r => r.weighting === 'VW')) {
  const q = (r.group === 'Strategy' ? strategies : cells).find(q => q.date!.slice(0, 7) === r.month)!;
  close(numeric(r.original_price_return), numeric(q[r.leg!]));
}
const robustness = csv(resolve(root, 'outputs/robustness.csv'));
close(numeric(dividendSummary.find(r => r.group === 'Strategy' && r.weighting === 'EW')!.original_price_spread_pp)! / 100, numeric(robustness.find(r => r.spec_id === 'equal_weight')!.primary_window_mean_spread));
for (const s of dividendSummary) {
  const rows = dividend.filter(r => r.group === s.group && r.weighting === s.weighting); const legs = [...new Set(rows.map(r => r.leg))];
  const g = rows.filter(r => r.leg === legs[0]), b = rows.filter(r => r.leg === legs[1]);
  assert.deepEqual(g.map(r => r.month), months(s.start!, s.end!)); assert.deepEqual(b.map(r => r.month), g.map(r => r.month));
  for (const [col, summaryCol] of [['original_price_return', 'original_price_spread_pp'], ['matched_price_conditional', 'matched_price_spread_pp'], ['total_fixed_weights_conditional', 'dividend_conditional_spread_pp']]) close(mean(g.map((r, i) => Number(r[col!]) - Number(b[i]![col!]))) * 100, numeric(s[summaryCol!]));
  close(Math.min(...rows.map(r => Number(r.original_weight_coverage))), numeric(s.min_weight_coverage));
  if (rows.some(r => Number(r.missing_n) > 0)) {
    assert.equal(s.complete_return_field_match, 'false'); for (const col of ['dividend_complete_spread_pp', 'self_financing_spread_pp', 'good_total_fixed_weights_cumulative_pct', 'bad_total_fixed_weights_cumulative_pct']) assert.equal(s[col], '');
  }
}
interface MatchingSummary { group: string; months: number; before_price_spread_pp: number; matched_price_spread_pp: number; dual_price_spread_pp: number; matched_total_spread_pp: number; expected_pair_months: number; observed_pair_months: number; dual_observed_pair_months: number; max_abs_post_smd: number; }
const monthly = csv(resolve(out, 'matching_monthly.csv')); const matching = json<MatchingSummary[]>(resolve(out, 'matching_summary.json')); const balance = csv(resolve(out, 'matching_balance.csv'));
for (const m of matching) {
  const q = monthly.filter(r => r.group === m.group); assert.equal(q.length, 58); assert.deepEqual(q.map(r => r.month), months('2021-07', '2026-04'));
  for (const [col, summaryCol] of [['before_price_spread', 'before_price_spread_pp'], ['matched_price_spread', 'matched_price_spread_pp'], ['dual_price_spread', 'dual_price_spread_pp'], ['matched_total_spread', 'matched_total_spread_pp']] as const) close(mean(q.map(r => Number(r[col]))) * 100, m[summaryCol]);
  assert.equal(q.reduce((v, r) => v + Number(r.observed_pairs), 0), m.observed_pair_months); assert.equal(q.reduce((v, r) => v + Number(r.matched_formation_pairs), 0), m.expected_pair_months);
  assert.equal(q.reduce((v, r) => v + Number(r.dual_observed_pairs), 0), m.dual_observed_pair_months);
  for (const r of q) assert(Number(r.dual_observed_pairs) <= Number(r.observed_pairs) && Number(r.observed_pairs) <= Number(r.matched_formation_pairs));
  close(Math.max(...balance.filter(r => r.group === m.group).map(r => Math.abs(Number(r.after_smd_original_sd)))), m.max_abs_post_smd);
}
const manifest = json<{ baseline_modified: boolean; matching: MatchingSummary[]; dividend: unknown[]; plan_sha256: string }>(resolve(out, 'summary.json'));
assert.equal(manifest.baseline_modified, false); assert.equal(manifest.plan_sha256, source.plan_sha256); assert.deepEqual(manifest.matching, matching);
assert.equal(manifest.dividend.length, dividendSummary.length);
for (const file of readdirSync(out).filter(f => /\.(csv|json)$/.test(f))) assert.equal(hash(resolve(out, file)), hash(resolve(root, 'dashboard/supplement', file)), 'stale Pages data: ' + file);
const page = readFileSync(resolve(root, 'dashboard/index.html'), 'utf8');
const embedded = JSON.parse(page.match(/<script id="research-data" type="application\/json">(.*?)<\/script>/s)![1]!);
assert.deepEqual(embedded, manifest);
for (const file of ['README.md', 'reports/RESEARCH_REPORT.md', 'reports/EXECUTIVE_BRIEF.md', 'docs/INTERVIEW_BRIEF.md', 'dashboard/index.html']) {
  const text = readFileSync(resolve(root, file), 'utf8'); assert(text.includes('사외이사 비율은 PBR 기반 종목선별을 보완하는가?'));
  for (const r of matching) for (const v of [r.before_price_spread_pp, r.matched_price_spread_pp]) assert(text.includes((v >= 0 ? '+' : '') + v.toFixed(4)), 'Missing claim evidence: ' + file);
  assert(!/\]\([^)]*\.pdf\)|(?:href|src)="[^"]*\.pdf"/i.test(text), 'PDF link remains in main research: ' + file);
  const links = [...text.matchAll(/\]\(([^)]+)\)|(?:href|src)="([^"]+)"/g)].map(m => m[1] ?? m[2]!);
  for (const link of links) if (!/^(https?:|#|data:)/.test(link)) assert(existsSync(resolve(dirname(resolve(root, file)), link.split('#')[0]!)), 'Broken local link: ' + file + ' ' + link);
}
for (const file of readdirSync(resolve(out, 'figures'))) if (file.endsWith('.svg')) assert.equal(hash(resolve(out, 'figures', file)), hash(resolve(root, 'dashboard/supplement', file)), 'stale Pages chart');
for (const file of readdirSync(out).filter(f => f.endsWith('.csv'))) {
  const header = Object.keys(csv(resolve(out, file))[0]!);
  assert(!header.some(k => ['stock_code','code','name','rcept_no','source_hash','financial_source_hash'].includes(k)), 'Private security records published');
}

// Failure mechanics: a missing weighted security is never promoted to a full return.
const partial = weightedMoment(new Map([['a', .9], ['b', .1]]), new Map([['a', .1], ['b', null]]));
close(partial.coverage, .9); close(partial.conditional, .1); assert.equal(partial.full, null);
const invalid = weightedMoment(new Map([['a', 1]]), new Map([['a', -1.1]])); assert.equal(invalid.full, null); assert.equal(invalid.conditional, null);
const member = (stock_code: string, cell: string, lag_me = 100, roe: number | null = .1, cohort = 2021): Member => ({ stock_code, cohort, cell, pbr_group: 'Low', lag_me, roe, pbr: .7 });
const synthetic = [member('g1','Low-Good'), member('g2','Low-Good',300), member('g3','Low-Good',100,null), member('b1','Low-Bad',110), member('b2','Low-Bad',320), member('b3','Low-Bad',100,.1,2022)];
const pairs = matchMembers(synthetic, plan); assert.equal(pairs.length, 2); assert.deepEqual(matchMembers([...synthetic].reverse(), plan), pairs, 'Matching must be deterministic');
for (const p of pairs) { assert.equal(p.good.cohort, p.bad.cohort); assert(p.good.roe !== null); }
assert.throws(() => cappedWeights(synthetic.slice(0, 3)), /infeasible/); const cap = cappedWeights([member('a','Low-Good',10000),...['b','c','d','e'].map(c => member(c,'Low-Good'))]); assert([...cap.values()].every(w => w <= .25 + 1e-12));
const privatePairs = resolve(root, '_workspace/supplement/matched_pairs.json');
if (existsSync(privatePairs)) for (const p of json<Pair[]>(privatePairs)) {
  assert.equal(p.good.cohort, p.bad.cohort); assert.equal(p.good.pbr_group, p.bad.pbr_group);
  assert(Math.abs(Math.log(p.good.lag_me / p.bad.lag_me)) <= plan.matching.max_abs_log_me_difference + 1e-12);
  assert(Math.abs(p.good.roe! - p.bad.roe!) <= plan.matching.max_abs_roe_difference + 1e-12);
  assert(Math.abs(Math.log(p.good.pbr / p.bad.pbr)) <= plan.matching.max_abs_log_pbr_difference + 1e-12);
}
console.log('PASS: protected evidence, original price replay, dividend coverage/NA, same-month matching, claims/charts, source privacy, missing-data and matching failure mechanics');
