import { mkdirSync, writeFileSync, copyFileSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { marked } from 'marked';
import { root, json, csv, numeric } from './research_io.js';

const repo = 'https://github.com/bucheoncityboy/mirae-governance-vfs-research';
const pages = 'https://bucheoncityboy.github.io/mirae-governance-vfs-research/';
const title = '사외이사 비율은 PBR 기반 종목선별을 보완하는가?';
const out = resolve(root, 'outputs/supplement'); const dashboard = resolve(root, 'dashboard');
interface Matching { group: string; before_price_spread_pp: number; matched_price_spread_pp: number; total_formation_pairs: number; observed_pair_months: number; expected_pair_months: number; dual_observed_pair_months: number; dual_price_spread_pp: number; matched_total_spread_pp: number; max_abs_post_smd: number; }
interface Dividend { group: string; weighting: string; original_price_spread_pp: number; matched_price_spread_pp: number; dividend_conditional_spread_pp: number; min_weight_coverage: number; expected_security_months: number; matched_security_months: number; }
interface Summary { question: string; baseline_modified: boolean; plan_sha256: string; matching: Matching[]; dividend: Dividend[]; }
interface OriginalPair { mean_monthly_good_minus_bad_pp: number; good_cumulative_pct: number; bad_cumulative_pct: number; months: number; formation_companies_by_cell: Record<string, number>; }
interface Core { H1_low_pbr_governance: OriginalPair; H2_high_pbr_governance: OriginalPair; cross_section: { groups: Record<string, { mean_monthly_good_minus_bad_pp: number }>; forward_loss_price_proxy: Record<string, Record<string, { complete_security_years: number; loss_security_years: number; loss_fraction: number }>> }; }
const summary = json<Summary>(resolve(out, 'summary.json')); const core = json<Core>(resolve(root, 'outputs/core_hypotheses/hypothesis_results.json'));
const low = core.H1_low_pbr_governance, high = core.H2_high_pbr_governance;
const match = (group: string): Matching => summary.matching.find(r => r.group === group)!;
const dividend = (group: string, weighting = 'VW'): Dividend => summary.dividend.find(r => r.group === group && r.weighting === weighting)!;
const pp = (v: number, digits = 4): string => (v >= 0 ? '+' : '') + v.toFixed(digits);
const pct = (v: number, digits = 2): string => v.toFixed(digits) + '%';
const table = (rows: (string | number)[][]): string => rows.map((r, i) => '| ' + r.join(' | ') + ' |' + (i === 0 ? '\n| ' + r.map(() => '---').join(' | ') + ' |' : '')).join('\n');
const formation = csv(resolve(root, 'outputs/core_hypotheses/formation_diagnostics.csv'));
const f = (cell: string, date: string, field: string): number => numeric(formation.find(r => r.cell === cell && r.date === date)![field])!;
const legacy = 'Value와 동일 조건으로 비교하는 공통 연속 기간은 2021-07~2021-12(6개월)입니다. 이 기간 누적 가격수익률은 VFS -11.14%, Value -13.72%, KOSPI -10.50%이며, VFS−Value 월평균 차이는 +0.43%p입니다.';
const conclusion = `**공시된 사외이사 비율만으로 VFS의 PBR×거버넌스 종목선별 논리를 안정적으로 구현했다고 판단하기는 어렵다.**

저PBR의 2021년 연속 가격경로에서는 사외이사 비율 상위 집단이 부진했고, 고PBR의 2022년 다른 기간에는 우위가 관측됐다. 같은 58개월 관측 단면에서 규모·PIT ROE·PBR이 유사한 기업으로 비교 대상을 제한하자 고PBR의 양의 차이는 축소됐고 저PBR의 차이는 음수였다. 또한 VFS의 Value 대비 상대성과는 시총가중과 동일가중에서 부호가 달랐다. 배당 포함 부분 표본도 이 민감도를 해소하지 못했다.

**따라서 이번 결과는 '거버넌스가 투자에 중요하지 않다'거나 '미래에셋 VFS 전략이 틀렸다'는 결론이 아니다.** 우리가 검증한 것은 MSCI의 복합 점수가 아닌 **사외이사 비율이라는 단일 공개 대리지표의 적용 가능성**이다. 이 지표만으로 추가적인 투자성과를 확인하기에는 근거가 부족하며, 종목선별에 활용하려면 기업규모·수익성·포트폴리오 가중치의 영향을 함께 평가해야 한다.

결론의 범위는 기존 공시 기반 형성군과 관측기간에 한정한다. 서로 다른 4~6개월 연속 가격경로, 관측 가능한 기업만 포함한 58개월 단면, 배당 포함 자료의 부분 커버리지, 기업행동·상폐 대가 및 독립 OOS 미검증으로 인해 장기 성과나 인과효과는 입증하지 않는다.`;
const executive = `**핵심 발견은 단일 대리지표의 선별 성과가 일관되지 않다는 점이다.** 사외이사 비율 상위 집단의 수익률은 저PBR의 짧은 연속 가격경로에서 열위였고, 다른 기간의 고PBR 경로에서는 우위였다. 58개월 관측 단면에서 규모·PIT ROE·PBR이 유사한 기업끼리 비교하면 고PBR의 양의 차이는 줄었고, VFS−Value도 가중 방식에 따라 부호가 바뀌었다. 이는 원문 MSCI G 전략에 대한 반증이 아니라 **공개 사외이사 비율 하나를 적용한 결과**다.`;
const purpose = `본 연구는 미래에셋증권 「멀티플 탈출」의 **PBR×거버넌스(VFS) 투자 아이디어**에서 출발해, 공개 공시자료의 **사외이사 비율**이 PBR 기반 종목선별에 보완적인 정보를 제공하는지 살펴본다. 원문의 MSCI Governance Score를 대체하거나 원문 장기 수익률을 재현하려는 연구가 아니라, **하나의 공개 대리지표를 적용했을 때 나타나는 결과와 제약**을 평가하는 독립 실증이다.`;
const toc = `- **Ⅰ. 서론 — 연구 배경과 설계:** 원문 VFS 아이디어, 공개 대리지표의 의미, 비교 기준
- **Ⅱ. 본론 — 실증 분석:** PBR 구간별 상대성과, 규모·ROE·PBR 매칭, VFS 구현 민감도
- **Ⅲ. 결론 — 투자적 시사점:** 사외이사 비율만으로 확인할 수 있는 범위와 남는 한계`;
const headline = table([
  ['검증하려는 주장', '핵심 실증', '판단'],
  ['같은 PBR 구간에서 Good이 우세한가?', `가격 Good−Bad: 저PBR ${pp(low.mean_monthly_good_minus_bad_pp)}%p/월(6개월), 고PBR ${pp(high.mean_monthly_good_minus_bad_pp)}%p/월(4개월)`, '방향이 일관되지 않으며 기간도 다름'],
  ['유사한 기업 특성에서도 차이가 남는가?', `58개월 관측 단면: 저PBR ${pp(match('Low').before_price_spread_pp)} → ${pp(match('Low').matched_price_spread_pp)}, 고PBR ${pp(match('High').before_price_spread_pp)} → ${pp(match('High').matched_price_spread_pp)}%p/월`, '매칭 표본에서 저PBR 음수·고PBR 양수'],
  ['투자 구현에 견고한가?', `VFS−Value: 시총가중 ${pp(dividend('Strategy').original_price_spread_pp)}, 동일가중 ${pp(dividend('Strategy', 'EW').original_price_spread_pp)}%p/월`, '가중 방식에 민감; 배당 포함은 부분 표본']
]);
const design = `PBR이 낮다는 사실만으로 저평가를 확정할 수 없고, 높다는 사실만으로 고평가를 확정할 수도 없다. 미래에셋증권 「멀티플 탈출」(2026-05-28)은 이런 문제의식에서 **PBR과 MSCI Governance Score를 결합**한 Value Focus Style(VFS)을 제안했다. 원문은 Low-Good과 High-Good에 각각 50%를 배분한다.

![원문의 PBR×G 투자 아이디어와 네 집단](outputs/supplement/figures/structure.svg)

**이 연구에서 달라지는 것은 G의 정의다.** 원문은 MSCI의 복합 거버넌스 평가를 사용하지만, 우리는 **공시된 사외이사 수/전체 이사 수**를 사용한다. 이하 Good·Bad는 각 PBR 구간 안에서 **사외이사 비율이 중앙값을 초과하는지**에 따른 기술적 분류일 뿐, 기업의 전반적인 거버넌스 품질을 인증하는 표현이 아니다. 따라서 우리의 결과를 원문 MSCI G의 성과나 거버넌스 개혁의 인과효과로 해석하지 않는다.

기존 검증된 공시 시점(PIT) 자료로 2021~2025년 다섯 연간 형성군을 만들고, 형성 시점의 PBR 중앙값으로 Low/High를 구분한다. 6월 말 이용 가능한 정보로 7월에 형성하며, 각 셀은 종목별 25% 상한 시총가중, VFS는 Low-Good/High-Good 50:50, Value 비교군은 Low-PBR 시총가중을 사용한다. 원래 보유 가격경로와 별도로 2021-07~2026-04 **58개월 관측 단면**을 분석하며, 둘을 하나의 장기 투자 NAV처럼 연결하지 않는다.

핵심 실증은 **같은 PBR 구간에서 사외이사 비율 상위/하위 집단의 상대성과**, **규모·PIT ROE·PBR 매칭 후 변화**, **가중치와 배당 포함 수익률의 민감도**다. 새 FnGuide 재무자료는 공시일이 확인되지 않아 PIT 종목선정이나 통제변수로 사용하지 않았다.`;
const finding1 = `**저PBR 연속 가격경로에서는 Good이 Bad보다 부진했고, 고PBR의 다른 연속기간에서는 Good이 우세했다.** 같은 형성 PBR 집단의 Good/Bad를 원래 시총 비중·연간 보유 규칙으로 비교한 결과다.

${table([
  ['공통 연속 가격기간', 'Good 누적', 'Bad 누적', 'Good−Bad 월평균', '형성 기업 Good / Bad', '보유 기업-월 Good / Bad'],
  ['저PBR · 2021-07~12 · 6개월', pct(low.good_cumulative_pct), pct(low.bad_cumulative_pct), pp(low.mean_monthly_good_minus_bad_pp) + '%p', '150 / 183', '900 / 1,098'],
  ['고PBR · 2022-07~10 · 4개월', pct(high.good_cumulative_pct), pct(high.bad_cumulative_pct), pp(high.mean_monthly_good_minus_bad_pp) + '%p', '124 / 177', '496 / 708']
])}

![저PBR의 Good 열위와 고PBR의 Good 우위는 서로 다른 연속기간에서 관측됐다](outputs/supplement/figures/pbr_spread.svg)

두 연속기간은 **같은 시장월이 아니므로 PBR 수준에 따른 효과 차이를 통계적으로 입증하지 않는다.** 같은 2021-07~2026-04의 58개월을 쓰는 별도 종목 평균 단면에서는 저PBR ${pp(core.cross_section.groups.Low!.mean_monthly_good_minus_bad_pp)}%p/월, 고PBR ${pp(core.cross_section.groups.High!.mean_monthly_good_minus_bad_pp)}%p/월이었다. 저PBR의 짧은 가격경로와 부호가 다르다. 이 단면은 매월 관측된 기업의 동일 평균으로 계산하며, 원래 시총 비중·결측 후 중단을 따르는 연속 가격경로와 기간·가중치·표본이 다르다. 결측 관측을 제외한 58개월을 투자 가능한 NAV로 연결하지 않았다.`;
const traitRows: (string | number)[][] = [['형성 특성 · 기업 단순 요약', 'Low-Good · 2021-07', 'Low-Bad · 2021-07', 'High-Good · 2022-07', 'High-Bad · 2022-07']];
traitRows.push(['PBR 중앙값', ...[['Low-Good','2021-07-01'],['Low-Bad','2021-07-01'],['High-Good','2022-07-01'],['High-Bad','2022-07-01']].map(([c,d]) => f(c!,d!,'pbr_median').toFixed(3))]);
traitRows.push(['시총 중앙값 · 십억원', ...[['Low-Good','2021-07-01'],['Low-Bad','2021-07-01'],['High-Good','2022-07-01'],['High-Bad','2022-07-01']].map(([c,d]) => (f(c!,d!,'lag_me_median') / 1e6).toFixed(2))]);
traitRows.push(['PIT ROE 평균 / 가용 기업 수', ...[['Low-Good','2021-07-01'],['Low-Bad','2021-07-01'],['High-Good','2022-07-01'],['High-Bad','2022-07-01']].map(([c,d]) => pct(f(c!,d!,'roe_mean') * 100) + ' / ' + f(c!,d!,'roe_observed_n'))]);
const finding2 = `**같은 58개월 관측 단면에서 특성이 유사한 기업 짝으로 표본을 제한하자 고PBR의 양의 차이가 줄고 저PBR의 차이는 음수로 바뀌었다.** Good은 원래 더 큰 기업으로 구성돼 있어 G만의 정보를 읽기 어렵다.

${table(traitRows)}

같은 형성연도·PBR 집단 안에서 규모 차이 2배 이내, PIT ROE 차이 5%p 이내, PBR 차이 1.5배 이내인 Good/Bad를 짝지었다. 허용된 짝의 정규화 거리 합이 작은 순서로, 수익률을 보지 않고 1:1·중복 없이 매칭했다. 결측 ROE를 양쪽에서 제외했으며 기준을 결과에 맞춰 바꾸지 않았다. 비교 전후 모두 **2021-07~2026-04의 같은 58개월**이고, 월별 동일 평균 차이를 다시 월 단순 평균했다.

${table([
  ['58개월 관측 가격 단면', '매칭 전 · PIT ROE 가용 표본', '매칭 후 · 양쪽 가격 가용 짝', '5개 형성군의 짝 수', '관측 짝-월 / 기대 짝-월'],
  ...summary.matching.map(m => [m.group === 'Low' ? '저PBR' : '고PBR', pp(m.before_price_spread_pp) + '%p/월', pp(m.matched_price_spread_pp) + '%p/월', m.total_formation_pairs, `${m.observed_pair_months.toLocaleString('en-US')} / ${m.expected_pair_months.toLocaleString('en-US')}`])
])}

![규모·PIT ROE·PBR 매칭 후 고PBR 차이는 줄고 저PBR 차이는 음수로 바뀌었다](outputs/supplement/figures/matching.svg)

형성연도별 log(시총)·ROE·log(PBR)의 매칭 후 절대 표준화 평균차는 모두 **${Math.max(...summary.matching.map(m => m.max_abs_post_smd)).toFixed(3)} 이하**였다. 이는 관측 특성의 평균 불균형이 작아졌다는 확인이며, 업종 등 미관측 차이가 없어졌다는 뜻은 아니다. 매칭 전 표본은 ROE 가용 기업이라 앞의 전체 단면(${pp(core.cross_section.groups.Low!.mean_monthly_good_minus_bad_pp)} / ${pp(core.cross_section.groups.High!.mean_monthly_good_minus_bad_pp)})과도 다르다. 매칭 전후는 동일 기간·PIT 가용성 기준을 공유하지만 기업 구성은 달라지고, 매칭 후에는 두 기업의 가격이 모두 관측된 짝만 월 평균에 쓴다. 이 때문에 차이의 축소를 규모·ROE가 설명한 인과적 비율로 계산하지 않는다.

고PBR의 잔여 ${pp(match('High').matched_price_spread_pp)}%p/월은 양의 관측 차이로 남지만, 독립적인 거버넌스 효과를 의미하지는 않는다. 저PBR에서는 이 방법으로 Good 우위를 확인하지 못했다. 5개 연간 형성군에서 반복 관측한 기술통계로, 유의한 알파·인과효과·완성된 매칭 전략 성과가 아니다. [매칭 월별 결과](outputs/supplement/matching_monthly.csv) · [형성군별 균형과 표본 수](outputs/supplement/matching_balance.csv).`;
const finding3 = `**VFS−Value와 고PBR Good−Bad의 차이는 가중 방식에 민감하며, 배당 포함 자료는 부분 표본에서만 확인됐다.** 원래 2021-07~12의 VFS 누적 가격수익률은 −11.14%, Value −13.72%, KOSPI −10.50%였다. VFS는 Value보다 손실이 작았지만 시장보다 부진했다. VFS−Value 월평균은 시총가중 ${pp(dividend('Strategy').original_price_spread_pp)}%p, 동일가중 ${pp(dividend('Strategy','EW').original_price_spread_pp)}%p로 반전됐다. 새로 같은 고PBR 4개월을 동일가중으로 재계산해도 Good−Bad가 ${pp(dividend('High','EW').original_price_spread_pp)}%p로 바뀌었다. 기업규모와 비중이 해석에 중요하다는 근거다.

FnGuide의 **KR_return_cash_dividend_included_pct**를 100으로 나눠 사용하고, **원래 종목·기간·가격경로의 월초 비중을 고정**했다. 전부 매칭되지 않아 각 셀·전략별 매칭 종목의 원래 비중을 다시 100%로 환산한 조건부 월평균만 계산했다. 같은 부분 표본의 기존 가격수익률을 옆에 두어 표본 변경과 수익률 기준 변경을 구분한다.

${table([
  ['비교 · 원래 공통기간', '가중', '전체 기존 가격 차이', '같은 부분 표본 가격 차이', '부분 표본 배당 포함 차이', '종목-월 매칭', '최저 원래 비중 커버리지'],
  ...summary.dividend.map(d => [d.group === 'Low' ? '저PBR · 6개월' : d.group === 'High' ? '고PBR · 4개월' : 'VFS−Value · 6개월', d.weighting === 'VW' ? '시총' : '동일', pp(d.original_price_spread_pp), pp(d.matched_price_spread_pp), pp(d.dividend_conditional_spread_pp), `${d.matched_security_months.toLocaleString('en-US')}/${d.expected_security_months.toLocaleString('en-US')}`, pct(d.min_weight_coverage * 100)])
])}

모든 차이는 %p/월이며, 커버리지는 비교하는 두 집단의 각 월 중 최저값이다. **배당 포함 열은 완전한 포트폴리오 수익률·누적 NAV가 아니다.** 시총가중 부분 표본의 저PBR 음수·고PBR 양수·VFS−Value 양수 방향은 유지됐고, 동일가중에서는 VFS−Value 음수도 유지됐다. 결측 종목의 수익률에 따라 전체 결과가 달라질 수 있어 부분 표본의 부호를 전체 총수익률의 검증으로 확대하지 않는다. 기존 가격과 새 수익률의 차이는 데이터 정의·가격 조정 차이도 포함할 수 있다.

![VFS의 Value 대비 차이는 배당 포함 부분 표본에서도 가중 방식에 따라 반전됐다](outputs/supplement/figures/implementation.svg)

매칭된 기업 짝에 배당 자료까지 있는 같은 월별 부분 표본에서도 저PBR은 가격 ${pp(match('Low').dual_price_spread_pp)} → 배당 포함 ${pp(match('Low').matched_total_spread_pp)}%p/월(${match('Low').dual_observed_pair_months.toLocaleString('en-US')} 짝-월), 고PBR은 ${pp(match('High').dual_price_spread_pp)} → ${pp(match('High').matched_total_spread_pp)}%p/월(${match('High').dual_observed_pair_months.toLocaleString('en-US')} 짝-월)로 부호가 유지됐다. 이는 같은 매칭 방법의 수익률 기준 민감도이며 추가 전략이 아니다.`.replaceAll('\\`', '`');
const appendix = `기존 결과·설계·원천 감사는 보존했다. 본문은 단일 연구 질문에 집중하며, 상세 기술자료는 다음 링크에서 확인할 수 있다.

[보완 분석 방법·재현](docs/SUPPLEMENT_REPRODUCIBILITY.md) · [기존 설계 잠금](config/vfs_pre_analysis_plan.yaml) · [결과 보기 전 고정한 보완 규칙](config/supplement_plan.json) · [기존 4셀 결과](outputs/core_hypotheses/hypothesis_results.json) · [상세 강건성](outputs/robustness.csv) · [기업행동 감사](docs/ECONOMIC_RETURN_RECOVERY.md) · [원천 검증](docs/PUBLIC_SOURCE_REBUILD.md) · [기존 상세 대시보드](dashboard/appendix.html) · [2026-10-11 핵심 분석 보존 페이지](dashboard/core-archive.html) · [면접 요약](docs/INTERVIEW_BRIEF.md) · [GitHub Pages](${pages})

${legacy}`;

const parts: [string, string][] = [
  ['Executive Summary', headline + '\n\n' + executive],
  ['01. Research Thesis & Design', design],
  ['02. Empirical Findings', '### Finding 1. 서로 다른 기간에 저PBR Good은 열위, 고PBR Good은 우위였다.\n\n' + finding1 + '\n\n### Finding 2. 유사 특성 표본에서 고PBR의 관측 차이는 작아졌다.\n\n' + finding2 + '\n\n### Finding 3. 배당 포함 부분 표본에서도 가중 방식의 영향은 남았다.\n\n' + finding3],
  ['03. Conclusion', conclusion], ['Appendix', appendix]
];
const readme = '# ' + title + '\n\n미래에셋 VFS 투자 아이디어에 대한 독립 실증 연구 · 2026-10-12\n\n' + parts.map(([h, b]) => '## ' + h + '\n\n' + b).join('\n\n') + '\n';
writeFileSync(resolve(root, 'README.md'), readme);
const relative = (text: string): string => text.replace(/\]\(([^)]+)\)/g, (_, link: string) => '](' + (link.startsWith('http') || link.startsWith('#') ? link : '../' + link) + ')');
writeFileSync(resolve(root, 'reports/RESEARCH_REPORT.md'), relative(readme));
writeFileSync(resolve(root, 'reports/EXECUTIVE_BRIEF.md'), relative('# ' + title + '\n\n' + headline + '\n\n' + executive + '\n\n' + conclusion + '\n\n' + legacy + '\n'));
writeFileSync(resolve(root, 'docs/INTERVIEW_BRIEF.md'), relative('# ' + title + '\n\n' + headline + '\n\n' + executive + '\n\n' + conclusion + '\n\n[연구 README](README.md) · [실증 대시보드](' + pages + ')\n'));

const figureDir = resolve(out, 'figures'); mkdirSync(figureDir, { recursive: true });
const escape = (v: string): string => v.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
function bars(filename: string, heading: string, subtitle: string, rows: { label: string; v: number; color: string }[], foot: string): void {
  const width = 960, height = 132 + rows.length * 70; const xmin = Math.min(-.1, ...rows.map(r => r.v)) * 1.3; const xmax = Math.max(.1, ...rows.map(r => r.v)) * 1.25;
  const x = (v: number): number => 380 + (v - xmin) / (xmax - xmin) * 500; const zero = x(0);
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img" aria-label="${escape(heading)}"><rect width="100%" height="100%" fill="#f8fafc"/><g font-family="Arial,Malgun Gothic,sans-serif"><text x="28" y="33" font-size="21" fill="#12243c" font-weight="700">${escape(heading)}</text><text x="28" y="58" font-size="14" fill="#53657a">${escape(subtitle)}</text><line x1="${zero}" x2="${zero}" y1="78" y2="${height - 57}" stroke="#9daab7"/>${rows.map((r, i) => {
    const y = 96 + i * 70;
    return `<text x="28" y="${y + 21}" font-size="16" fill="#263b53">${escape(r.label)}</text><rect x="${Math.min(zero, x(r.v))}" y="${y}" width="${Math.abs(x(r.v) - zero)}" height="32" rx="3" fill="${r.color}"/><text x="${x(r.v) + (r.v >= 0 ? 10 : -10)}" y="${y + 22}" text-anchor="${r.v >= 0 ? 'start' : 'end'}" font-size="17" fill="#12243c" font-weight="700">${pp(r.v)}</text>`;
  }).join('')}<text x="28" y="${height - 20}" font-size="13" fill="#53657a">${escape(foot)}</text></g></svg>`;
  writeFileSync(resolve(figureDir, filename), svg);
}
bars('pbr_spread.svg', '저PBR Good은 열위, 고PBR Good은 우위', '원래 시총가중 가격경로 · 월평균 Good−Bad (%p)', [{ label: '저PBR · 2021-07~12 · 6개월', v: low.mean_monthly_good_minus_bad_pp, color: '#bf633d' }, { label: '고PBR · 2022-07~10 · 4개월', v: high.mean_monthly_good_minus_bad_pp, color: '#245b8c' }], '기간이 서로 다름 · PBR 효과 차이 검정 아님 · 통계적 추론 미추정');
bars('matching.svg', '특성을 맞추자 고PBR 우위는 줄었다', '동일 58개월 · PIT ROE 가용 관측 가격 · 월평균 Good−Bad (%p)', summary.matching.flatMap(m => [{ label: (m.group === 'Low' ? '저PBR' : '고PBR') + ' · 매칭 전', v: m.before_price_spread_pp, color: '#b4c1cf' }, { label: (m.group === 'Low' ? '저PBR' : '고PBR') + ' · 규모·ROE·PBR 매칭 후', v: m.matched_price_spread_pp, color: '#245b8c' }]), '2021-07~2026-04 · 5개 형성군 · 구성·결측 선택이 달라짐 · NAV·인과효과 아님');
bars('implementation.svg', 'VFS−Value는 가중 방식에 따라 반전됐다', '같은 2021-07~12 · 6개월 · 월평균 차이 (%p)', ['VW', 'EW'].flatMap(w => [{ label: (w === 'VW' ? '시총가중' : '동일가중') + ' · 전체 가격', v: dividend('Strategy', w).original_price_spread_pp, color: '#245b8c' }, { label: (w === 'VW' ? '시총가중' : '동일가중') + ' · 배당 포함 부분 표본', v: dividend('Strategy', w).dividend_conditional_spread_pp, color: '#bf633d' }]), '배당 포함은 원래 월초 비중의 매칭 부분 표본 · 완전한 총수익률·누적 NAV 아님');
writeFileSync(resolve(figureDir, 'structure.svg'), `<svg xmlns="http://www.w3.org/2000/svg" width="960" height="270" viewBox="0 0 960 270" role="img" aria-label="PBR과 거버넌스의 네 집단"><rect width="960" height="270" fill="#f8fafc"/><g font-family="Arial,Malgun Gothic,sans-serif" fill="#12243c"><text x="28" y="35" font-size="20" font-weight="700">PBR × 거버넌스: 원문 투자 논리와 검증 대상</text><text x="230" y="76" font-size="16">Low-PBR</text><text x="620" y="76" font-size="16">High-PBR</text><rect x="180" y="95" width="330" height="64" fill="#dfeaf4" rx="6"/><rect x="560" y="95" width="330" height="64" fill="#dfeaf4" rx="6"/><text x="30" y="131" font-size="17">Good-G</text><text x="210" y="122" font-size="17">재평가 가능성 · VFS 50%</text><text x="210" y="146" font-size="13">저평가 + 양호한 거버넌스</text><text x="590" y="122" font-size="17">멀티플 유지 · VFS 50%</text><text x="590" y="146" font-size="13">높은 PBR + 양호한 거버넌스</text><text x="30" y="209" font-size="17">Bad-G</text><text x="210" y="200" font-size="17">가치 함정 가능성</text><text x="590" y="200" font-size="17">고평가 + 거버넌스 위험</text><text x="28" y="250" font-size="13" fill="#53657a">우리 연구의 G는 공시 사외이사 비율 · 원문 MSCI G와 다름 · 네 셀의 예상 논리를 독립 검증</text></g></svg>`);
const assetDir = resolve(dashboard, 'supplement'); mkdirSync(assetDir, { recursive: true });
for (const name of readdirSync(out)) if (/\.(csv|json)$/.test(name)) copyFileSync(resolve(out, name), resolve(assetDir, name));
for (const name of readdirSync(figureDir)) if (name.endsWith('.svg')) copyFileSync(resolve(figureDir, name), resolve(assetDir, name));
const slug = (heading: string): string => heading.startsWith('01.') ? 'thesis' : heading.startsWith('02.') ? 'findings' : heading.startsWith('03.') ? 'conclusion' : heading === 'Appendix' ? 'appendix' : 'executive';
const browserMd = (text: string): string => text.replace(/\]\(([^)]+)\)/g, (_, link: string) => '](' + (link.startsWith('outputs/supplement/figures/') ? 'supplement/' + link.split('/').at(-1)! : link === 'dashboard/appendix.html' ? 'appendix.html' : link === 'dashboard/core-archive.html' ? 'core-archive.html' : link.startsWith('http') || link.startsWith('#') ? link : repo + '/blob/main/' + link) + ')');
const style = `:root{color-scheme:light;--ink:#12243c;--muted:#53657a;--line:#dce4ec;--accent:#245b8c}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#fff;color:var(--ink);font:16px/1.8 Arial,"Malgun Gothic",sans-serif}a{color:var(--accent);text-underline-offset:4px}header,main,footer{max-width:1120px;margin:auto;padding:28px 32px}header{padding-top:44px;border-bottom:1px solid var(--line)}.eyebrow{font-size:12px;letter-spacing:.16em;color:var(--muted)}h1{font-size:clamp(28px,4vw,46px);line-height:1.3;margin:16px 0}nav{display:flex;gap:24px;flex-wrap:wrap;margin:24px 0 0;font-size:14px}section{padding:26px 0 38px;border-bottom:1px solid var(--line)}h2{font-size:24px;line-height:1.4;margin:18px 0 24px}h3{font-size:20px;line-height:1.5;margin:38px 0 18px}p{margin:18px 0;max-width:100%}table{width:100%;border-collapse:collapse;font-size:14px;line-height:1.55;margin:22px 0}th{text-align:left;background:#edf2f7;color:var(--ink);padding:12px 10px}td{padding:13px 10px;border-bottom:1px solid var(--line);vertical-align:top}img{display:block;width:100%;height:auto;margin:24px 0;border:1px solid var(--line);border-radius:8px}strong{font-weight:700}#conclusion{border-top:3px solid var(--accent);background:#f8fafc;padding:24px;margin-top:18px}footer{font-size:13px;color:var(--muted)}.table-wrap{overflow-x:auto}#appendix p{font-size:14px}@media(max-width:700px){header,main,footer{padding-left:18px;padding-right:18px}body{font-size:15px}h2{font-size:22px}h3{font-size:19px}table{min-width:650px}nav{gap:14px}#conclusion{padding:16px}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}`;
const body = parts.map(([heading, text]) => `<section id="${slug(heading)}"><h2>${escape(heading)}</h2>${String(marked.parse(browserMd(text), { async: false })).replaceAll('<table>', '<div class="table-wrap"><table>').replaceAll('</table>', '</table></div>').replace(/<p>(<img[^>]+>)<\/p>/g, '<div class="chart-wrap">$1</div>')}</section>`).join('\n');
const scripts = [['research-data', summary], ['core-hypotheses-data', core], ['result-data', json<unknown>(resolve(root, 'outputs/public_result_summary.json'))], ['final-evidence-data', json<unknown>(resolve(root, 'outputs/final/completion_status.json'))]].map(([id, data]) => `<script id="${id}" type="application/json">${JSON.stringify(data).replaceAll('<', '\\u003c')}</script>`).join('');
const page = `<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="PBR에 거버넌스가 추가 정보를 제공하는지 가격경로, PIT 규모·ROE 매칭, FnGuide 배당 민감도로 검증한 독립 연구"><title>${title} | 독립 VFS 연구</title><style>${style}.chart-wrap{overflow-x:auto}@media(max-width:700px){.chart-wrap img{min-width:700px}}</style></head><body><header><p class="eyebrow">INDEPENDENT VFS RESEARCH · 2026-10-12</p><h1>${title}</h1><p>미래에셋 VFS 투자 아이디어에 대한 독립 실증 연구</p><nav aria-label="연구 목차"><a href="#thesis">Research Thesis</a><a href="#findings">Empirical Findings</a><a href="#conclusion">Conclusion</a><a href="#appendix">Appendix</a><a href="${repo}">README · 코드</a></nav></header><main>${body}${scripts}</main><footer>공개 결과는 집계 자료입니다. 비공개 FnGuide 원천·종목별 입력·API 키는 게시하지 않았습니다.</footer></body></html>\n`;
writeFileSync(resolve(dashboard, 'index.html'), page);
console.log('RESEARCH_PUBLICATION_GENERATED_FROM_VERIFIED_AGGREGATES');
