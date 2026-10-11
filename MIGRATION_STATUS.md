# Migration and acceptance status - 2026-10-11 KST

**Source repository separation: COMPLETED after user-approved PR #2 merge on 2026-10-11 KST.** The FF repository main now contains only the 120 original protected files. VFS research remains partially observed / EMPIRICAL_LIMITED; VFS own history is eight months, the paired comparison six. The portfolio-index PR #1 is merged and verified on public main.

| Repository / artifact | Verified state |
| --- | --- |
| New public repo | https://github.com/bucheoncityboy/mirae-governance-vfs-research |
| Publication HEAD at initial CI/Pages verification | 7eaae94cdd66f82bd966c55e21d3bed7f2b02fd5; later acceptance commits are in main history |
| Before-outcomes design commit | 09a105ce651bc28eaad1e0993b12678a41acf61f |
| Original source main HEAD after approved separation | dc47a81b214cfb1aac210d0568938eb652f75b03; governance directory/workflow absent |
| Original cleanup commit / merged PR | 8b8873bc383f7ca7ed1caab82439fa42b793ccb8 / https://github.com/bucheoncityboy/fama-french-integrated-research/pull/2 |
| Approved merge commit | https://github.com/bucheoncityboy/fama-french-integrated-research/commit/dc47a81b214cfb1aac210d0568938eb652f75b03 |
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
| merged | cleanup PR #2: true (explicit user approval); portfolio PR #1: true (subsequent user request). No force-push or default-branch change |

## Validation gates

- GATE A: PASS_DIAGNOSTIC_ONLY. 4,540 G / 4,382 financial observations and 9,186 raw objects reverified. 782 companies / 38,742 joint stock-months. Only 8 common valid months, longest 6 (2021.07-12). Investable total-return validation UNVERIFIED.
- GATE B: PASS_WITH_DOCUMENTED_ADAPTATIONS. Outside-director ratio, price returns, median cutoffs, June information/July entry, no added winsorization; formation-only cap timing explicit.
- GATE C: LOCKED_EXPLORATORY. Remote lock before new outcomes; prior results known. D004 fixes initial cost accounting without changing gross returns; D005 adds registered descriptive controls only.
- VFS own-return result: 2021.07-2022.02, eight observed months, cumulative -17.30% versus same-period KOSPI -18.96%. This does not replace the locked six-month paired Value comparison. Direct price/RF ingestion removes the VFS engine's FF3-factor dependency.
- GATE D/F: VFS_DATA_PARTIAL / AUXILIARY_FF3_MIN24_NOT_MET. FF3 alpha/t/p/CI and spread HAC inference remain NOT_ESTIMATED. No independent OOS.
- GATE E: 5 PASS / 10 UNVERIFIED / 1 FAIL. Original full US suite separately UNRESOLVED; compatible rerun 235 passed / 23 failed / 16 errors / 1 skipped. Offline regression subset 92 passed. See docs/ORIGINAL_REGRESSION_CHECK.md.
- GATE G: PASS_LIMITED_DIAGNOSTICS. Eight actual-data PNG/SVG exhibits, including a separate VFS own-return path; dashboard and ten-page PDF; alpha CI/12-month rolling volatility NOT_ESTIMATED.
- GATE R: PASS_LIMITED_NARRATIVE. Every p2 contents entry mapped; source and independent results labelled; identical public inputs; actual local/external links and desktop/mobile rendering checked.
- GATE H: PASS_MERGED_VERIFIED. Minimal portfolio row reflects limited results, live PDF/Pages, academic FF3 unchanged.

Publication inventory and 133 immutable legacy copy hashes: [manifest](docs/migration_manifest.csv). FnGuide security rows, DART bodies, credentials, unreviewed history bundle and original Mirae PDF remain excluded. Public outputs contain aggregates only; source-data redistribution rights remain UNVERIFIED. No blanket third-party license is claimed.

Unresolved research issues: historical listing/delisting/terminal payoffs, dividend/corporate-action total returns, original-before-correction filings, industry/liquidity/legal-entity assets, independent OOS, and original US full-suite input/environment issues. They do not change the verified source separation: remote main tree equals baseline 81f3bd9, all 120 protected blobs match, and the legacy snapshot 133 blobs match the copied source. [Separation verification](docs/SEPARATION_VERIFIED.json).

Portfolio public main merge commit: [f3e9afe166613c4fc61f20c02356428b56d1931d](https://github.com/bucheoncityboy/portfolio-index/commit/f3e9afe166613c4fc61f20c02356428b56d1931d). Old standalone repository: all 52 files copied immutably, all refs backed up locally and verified; repository deletion completed after explicit user approval and GitHub Mobile administrator authentication. GitHub success banner, old public URL/API HTTP 404, and live new repo/report/dashboard HTTP 200 verified. [Retirement record](docs/STANDALONE_RETIREMENT.md).

## 2026-10-11 final limited-evidence extension

Latest checked main before this extension: d6b379508a913346d74387c046f80ed0f8e65a7d (README PR #2 merged after successful CI under the user's new autonomous-merge authorization). Economic follow-up lock commit: 91e39d7736a108fb0b105c77ba173fae9e60b302. Existing primary and reconstruction/multiplicity locks unchanged.

Current-source offline raw rerun: PASS, five aggregate CSVs byte-identical; published monthly VFS/Value/Market differences >1e-12: zero. Eleven unique held events / 13 strategy records: official bodies of 16 receipts / 37 sections read; zero monthly economic-return repairs. Owner backup rehash 39,552 files / 301,339,448 bytes / zero failures; credential excluded. Four private follow-up handoff files copied and hashed, with personal details in official bodies excluded. No new source/security rows published.

Final scientific classification: COMPLETE_LIMITED_EVIDENCE; actual backtest remains EMPIRICAL_LIMITED. VFS own N=8, common N=6, G-neutral N=2; FF3/HAC/CI NOT_ESTIMATED, OOS UNVERIFIED. December rights transitions and pre-formation trading halts strengthen the stated investability limitation. Existing reports archived byte-exact; updated report ten pages, executive PDF two pages, rebuild appendix three pages. Final local suite: 60 passed, public verification PASS, all source FF3 trees/data unchanged. Publication receipts are recorded after actual PR checks/deployment rather than claimed in advance.
