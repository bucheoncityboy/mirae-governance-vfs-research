# Original FF3 regression checks - full suite not clean

The 120 protected files remain byte-identical to baseline 81f3bd9 after both test attempts. The cleanup proposed Git tree is exactly 7d366a75c62e1f2f5dd1b8817222a75adb6933bd, identical to that baseline. This establishes no source-code or original-data change; it does not declare the legacy full suite healthy.

Initial local Python 3.12 / pandas 3.x environment: **204 passed / 40 failed / 30 errors / 1 skipped**, including missing pandas-datareader. An isolated environment was prepared with pandas 2.2.3, statsmodels 0.14.6 and pandas-datareader 0.11.1; no original source files were modified.

Compatibility rerun: **235 passed / 23 failed / 16 errors / 1 skipped** (126.22s). Residual failures include missing expected `us-ff1993/data/ff_factors.csv`, factor file shape/date/column expectations, original bond-factor/FRED input paths and portfolio source behavior. They remain explicit; fixing original US research would exceed the immutable-source boundary. The full legacy suite remains **UNRESOLVED**. Separately, the source-separation PR #2 was reviewed and merged after explicit user approval on 2026-10-11 KST. Its resulting main tree exactly equals original baseline 81f3bd9; no protected FF3 source/input was modified.

Separate offline core regression/intercept/GRS subset: **92 passed** (11.74s) in the compatible environment. This narrower success does not erase the full-suite failures. All 120 protected original files still match baseline after the runs.

After the approved merge, the actual main checkout was updated to dc47a81 and the same core subset rerun: **92 passed** (15.27s). Remote main contains 120 files and exactly the original baseline tree; the governance directory and workflow are absent.

Original successful governance CI is separately recorded in [legacy evidence](LEGACY_CI_EVIDENCE.md). New VFS public validation passes independently. Full log is retained locally outside the public dataset; no authentication values are reproduced.
