# Printed contents to independent validation - GATE R evidence index

Official p2 Contents was directly verified; every contents entry is mapped below. All functions are in `src/vfs_research`. Tests in `tests/test_engine.py`, public outputs in `outputs`. Original narrative claims are paraphrases, independent tests are explicitly OUR EXTENSION.

| Printed page | Actual contents title / evidence | Original claim role | Our hypothesis / implementation | Evidence / test | Status and limitation |
| --- | --- | --- | --- | --- | --- |
| 3 | Executive Summary | VFS pairs governance with value | H1-H3; backtest.run | performance_summary.csv, test_public_consistency | ADAPTED; six-month price diagnostic |
| 5 | 두개의 날개, 반도체와 거버넌스 개혁 | Semiconductor/policy background | README 01 background | Original source only | CONTEXT_ONLY; macro causality not tested |
| 5 | 비상하는 코스피와 두개의 날개: 반도체와 거버넌스 개혁 | Market interpretation | README 01 | Original source only | CONTEXT_ONLY |
| 8 | 거버넌스 개혁, 이제 시작입니다만? | Reform timing | README 01 | No reform event study | NOT_TESTED |
| 10 | 코스피의 적정 멀티플을 찾아서 | ROE/COE justified valuation | README 02 | No eight-factor COE implementation | CONTEXT_ONLY / NOT_TESTED |
| 11 | 코스피 적정 PBR 3.5배, 적정 PER 15배 | Valuation scenario | README 02 | Original-only facts | NOT_TESTED |
| 11 | 코스피 적정 멀티플 시나리오 분석 - Bull·Base·Bear | Scenario model | README 02 | No estimates | NOT_TESTED |
| 13 | 임박한 코리아 프리미엄 | Governance discount interpretation | README 02 | No causal test | CONTEXT_ONLY |
| 15 | 삼성전자·SK하이닉스가 없었다면? | Semiconductor concentration | H4; exclude_universe_top5 sensitivity is a different test | robustness.csv | ADAPTED; sector PIT attribution NOT_TESTED |
| 17 | 코스피 아웃퍼폼의 조건 | Value vs growth performance | H1/H3; backtest.run | monthly_returns.csv, cumulative.png | ADAPTED; common months only |
| 17 | 성장주와 가치주가 모두 상승하는 복합장세 | Style regime background | README 03 | annual_returns.csv | CONTEXT_ONLY; incomplete VFS years |
| 18 | 시장은 지금 무엇에 반응하고 있는가? | Style interpretation | README 03 | No event identification | NOT_TESTED |
| 20 | 밸류 포커스 스타일 (Value Focus Style); table 6 | PBR × G sorting | universe.eligible, sorts.classify | test_ties, cell_formation_coverage.csv | REIMPLEMENTED rule, ADAPTED G definition |
| 21 | table 7 / figures 37-38 (body evidence) | Cap, annual rebalance and returns | portfolio.capped_weights, backtest.run | cap tests, performance_summary.csv | ADAPTED; PRICE_RETURN_ONLY and six months |
| 22 | tables 8-9 (body evidence) | Top constituents / style rationale | Aggregated size/ROE exposure | formation_summary.csv | ADAPTED; original securities not cloned; sector NOT_TESTED |
| 23 | table 10 (body evidence) | Style correlations / MSCI coverage | H4; bias_audit.audit_all | size_G_diagnostics.csv, robustness.csv | ADAPTED size diagnostic; FF3 betas NOT_ESTIMATED |
| 25 | 결론: 멀티플 탈출의 조건 | Interpretation | README 07 independent conclusion | results_status.json | ADAPTED; no alpha or causal claim |
| 25 | 할인율 방향 전환 | COE hypothesis | README 07 | No COE estimator | NOT_TESTED |
| 25 | 베타는 왔지만 알파는 아직이다 | Governance reward interpretation | H2 stats.regression (OUR EXTENSION) | ff3_alphas.csv, RF test | NOT_ESTIMATED; original use of alpha is not FF3 table-7 alpha |
| 25 | 가격이 아닌 가격의 이유에 베팅하라 | Strategy rationale | README 07 | Diagnostic returns | ADAPTED; does not establish governance quality |
| 26 | Appendix | Method appendix | README Appendix A | Scope statement | CONTEXT_ONLY |
| 26 | 자기자본비용의 추정; figure 39 actually p27 | Multifactor COE and MSCI score | Appendix A | No COE implementation | NOT_REPLICATED |
| 28 | 밸류 포커스 스타일 다기간 검증; figures 40-42 | Annual returns / Sharpe | H2/H5 stats, bias_audit (OUR EXTENSION) | annual_returns.csv, bootstrap.json, bias_audit.csv | NOT_ESTIMATED VFS full years; OOS NOT VERIFIED |

FF3, paired spread inference, PIT, survival, multiple testing and independent OOS are our independent extensions. None are labelled exact reproductions of the official report. The README follows original main sections, then our p28 extension and conclusion. It does not infer a significant governance premium from a short curve.
