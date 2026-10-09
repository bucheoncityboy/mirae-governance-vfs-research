# Migration and acceptance status - 2026-10-10 KST

**Overall: VFS backtest partially observed / EMPIRICAL_LIMITED.** VFS's own longest contiguous history is eight months; the locked Value/Market paired comparison is six. FF3 is an auxiliary attribution test with insufficient observations. Remaining total-return/corporate-action/history gaps prevent full empirical completion. Source separation and portfolio listing remain unmerged PRs.

| Repository / artifact | Verified state |
| --- | --- |
| New public repo | https://github.com/bucheoncityboy/mirae-governance-vfs-research |
| Publication HEAD at initial CI/Pages verification | 7eaae94cdd66f82bd966c55e21d3bed7f2b02fd5; later acceptance commits are in main history |
| Before-outcomes design commit | 09a105ce651bc28eaad1e0993b12678a41acf61f |
| Original source main HEAD | 7e7eb6a41e1d798f45d10b96e704e6c476cd6091 - unchanged |
| Original cleanup commit / Draft PR | 8b8873bc383f7ca7ed1caab82439fa42b793ccb8 / https://github.com/bucheoncityboy/fama-french-integrated-research/pull/2 |
| Original 120-file SHA256 | PASS, original US/Korean FF3 source/data/PDF/README unchanged |
| Cleanup proposed tree | 7d366a75c62e1f2f5dd1b8817222a75adb6933bd - exactly baseline 81f3bd9; only 141 governance/workflow files removed |
| Initial main CI | https://github.com/bucheoncityboy/mirae-governance-vfs-research/actions/runs/37985851830 - success |
| Initial Pages deployment | https://github.com/bucheoncityboy/mirae-governance-vfs-research/actions/runs/37985851923 - success |
| Real dashboard | https://bucheoncityboy.github.io/mirae-governance-vfs-research/ - HTTP 200; HTML/CSV/SVG hashes match local |
| Report | reports/RESEARCH_REPORT.pdf - ten pages, Korean text and charts visually checked |
| portfolio_index_repo | https://github.com/bucheoncityboy/portfolio-index |
| readme_old_head_sha | f6cd0f0332e9ecd599985cba4d1a94a9e2b40b68 |
| readme_new_branch_commit | 07233f813afa5f7d9d236fde7cabf8de032d2ab8 |
| portfolio_index_pr_url | https://github.com/bucheoncityboy/portfolio-index/pull/1 |
| new_vfs_repo_link_ok / report_link_ok / dashboard_link_ok | true / true / true |
| portfolio change scope | One HTML row; other content byte-identical; academic FF3 row preserved |
| render_check | GitHub preview and desktop/mobile dashboard checked; seven images loaded; 390px dashboard has no horizontal overflow |
| merged | false for both PRs; no merge, force-push or default-branch change |

## Validation gates

- GATE A: PASS_DIAGNOSTIC_ONLY. 4,540 G / 4,382 financial observations and 9,186 raw objects reverified. 782 companies / 38,742 joint stock-months. Only 8 common valid months, longest 6 (2021.07-12). Investable total-return validation UNVERIFIED.
- GATE B: PASS_WITH_DOCUMENTED_ADAPTATIONS. Outside-director ratio, price returns, median cutoffs, June information/July entry, no added winsorization; formation-only cap timing explicit.
- GATE C: LOCKED_EXPLORATORY. Remote lock before new outcomes; prior results known. D004 fixes initial cost accounting without changing gross returns; D005 adds registered descriptive controls only.
- VFS own-return result: 2021.07-2022.02, eight observed months, cumulative -17.30% versus same-period KOSPI -18.96%. This does not replace the locked six-month paired Value comparison. Direct price/RF ingestion removes the VFS engine's FF3-factor dependency.
- GATE D/F: VFS_DATA_PARTIAL / AUXILIARY_FF3_MIN24_NOT_MET. FF3 alpha/t/p/CI and spread HAC inference remain NOT_ESTIMATED. No independent OOS.
- GATE E: 5 PASS / 10 UNVERIFIED / 1 FAIL. Original full US suite separately UNRESOLVED; compatible rerun 235 passed / 23 failed / 16 errors / 1 skipped. Offline regression subset 92 passed. See docs/ORIGINAL_REGRESSION_CHECK.md.
- GATE G: PASS_LIMITED_DIAGNOSTICS. Eight actual-data PNG/SVG exhibits, including a separate VFS own-return path; dashboard and ten-page PDF; alpha CI/12-month rolling volatility NOT_ESTIMATED.
- GATE R: PASS_LIMITED_NARRATIVE. Every p2 contents entry mapped; source and independent results labelled; identical public inputs; actual local/external links and desktop/mobile rendering checked.
- GATE H: PASS_PR_VERIFIED_MERGE_PENDING. Minimal portfolio row reflects limited results, live PDF/Pages, academic FF3 unchanged.

Publication inventory and 133 immutable legacy copy hashes: [manifest](docs/migration_manifest.csv). FnGuide security rows, DART bodies, credentials, unreviewed history bundle and original Mirae PDF remain excluded. Public outputs contain aggregates only; source-data redistribution rights remain UNVERIFIED. No blanket third-party license is claimed.

Unresolved: complete historical listing/delisting/terminal payoffs, dividend/corporate-action total returns, original-before-correction filings, historical industry/liquidity/legal-entity assets, sufficient independent OOS, and original US full-suite input/environment issues. Successful software CI and formatted artifacts do not resolve empirical blockers. Post-merge regression cannot be checked before user review and merge.
