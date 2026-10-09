# VFS backtest first: observed history, paired comparison, auxiliary attribution

The primary task is to implement Mirae's VFS allocation, holdings, annual rebalance and return path, then compare Value and Market. FF3 is a supplementary attribution test. Its 24-month condition does not determine whether VFS raw-return backtesting exists.

## What the actual return file supports

- VFS: 10 valid months across two disconnected segments; longest contiguous history **2021.07-2022.02, 8 months**. No gap is bridged.
- VFS/Value/Market paired comparison: 8 common valid months across segments; longest **2021.07-12, 6 months**. The previously locked comparison is preserved.
- VFS own 8-month cumulative price return **-17.30%**, same-period KOSPI **-18.96%**. These cannot be combined with six-month Value returns as if the periods matched.
- The direct KOSPI benchmark/RF file now feeds the VFS backtest. No SMB/HML or FF3 fit is required. FF3 joins happen only in the supplementary factor-test stage.

[VFS own metrics](../outputs/vfs_strategy_summary.csv), [observed segments](../outputs/observed_segments.csv), [paired monthly history](../outputs/monthly_returns.csv), [break audit](../outputs/vfs_missing_breaks.csv).

## The restrictive missing-return rule is our assumption

The original report does not explicitly prescribe stopping the remainder of an annual holdings path after one missing asset return. We locked this conservative rule to avoid unsupported terminal-payoff guesses, zero filling, future-survivor selection or ex-post reweighting. It materially shortens the displayed history; it is not a financial law or an original Mirae rule.

Each annual path's first break was checked against the complete `stock_returns.parquet`, independently of the governance/FF3 formation panel. All 13 strategy break records still lack a valid return there. Among the 7 VFS asset-break records, 4 have no matching raw price and 3 were affected by the inherited absolute-price-return >100% filter. For Value the corresponding counts are 4 and 2, across 6 records. These counts are asset-break records, not unique firms. No delisting, merger, split or actual economic return is inferred from a missing row alone.

The unknown holdings often have small portfolio weights. Size alone cannot justify assigning them zero returns or silently deleting them. Recovering official corporate-action/terminal cashflow and adjusted-price evidence is the next data task; weakening the rule to obtain a longer attractive curve is not a repair.

## Reporting correction

VFS observed holdings/performance comes first; matched Value/Market comparison uses its own labelled common window; FF3, tests and prior US FF3 migration evidence are supplementary. D006 records this dependency/presentation correction after outcomes. Strategy thresholds, annual formation, capped weights and the previously locked paired comparison are unchanged.
