# Implementation assumptions - locked before outcomes

This independent implementation uses outside-director ratio, not the MSCI governance score. Prior FF3 G pilot results were already known. No causal or confirmatory claim is justified.

1. Positive verified fiscal t-1 equity / contemporaneous June market capitalization defines PBR. ME is thousands KRW, BE is 100 million KRW: PBR = ME / (BE × 100,000). Verified source statement scope CFS/OFS is retained; preferred shares and financials are not independently certified and are not silently excluded.
2. Form on the June KRX month-end using only already-public annual filings; returns start July. Hold for 12 months with drift. July formation is our PIT convention; the original exact annual date is unreported. One-month delay is a separate sensitivity using current cap / available BE.
3. Median PBR, ties Low; median G within each PBR group, ties Bad. No artificial tie splitting. MSCI/PBR original cut points are not recoverable.
4. VFS uses capped market-cap weights in Low-Good and High-Good, 50% each. Cap redistribution converges or the cell is invalid. We enforce 25%/12.5% at formation. Holding-period drift can exceed that limit; continuous capping would require extra transactions incompatible with an unqualified annual rebalance claim. The original cap timing is not explicit.
5. Value uses all Low-PBR stocks from the same formation-time eligible set, uncapped cap weights. Benchmark is the original KOSPI price-return series reconstructed as Mkt-RF + RF. Neither is the original FnGuide/MSCI total-return implementation.
6. Missing held return invalidates that strategy through the next annual reset. No future-sample conditioning, zero fill, survivor selection or ex-post renormalization. Other strategies can remain valid independently; the common window additionally requires both longs and Market.
7. No added winsorization: original quantile is unreported. The inherited >100% filter is audited, not blessed. No company-action payoff is guessed.
8. Costs are one-way 0/10/30bp on total buys plus sells; net=(1-cost×traded_weight)×(1+gross)-1. Initial funding buys one portfolio. Reset turnover following an unknown holdings path is NA. Taxes, slippage, shorting, financing and liquidity capacity are unverified. No theoretical long-short performance is presented as tradable.
9. Long returns subtract RF once. VFS-Value spread subtracts RF zero times. HAC3/HAC6 with finite-sample correction and Student-t CI requires at least 24 contiguous months; <24 is NOT_ESTIMATED. CAGR/Sharpe over the six-month diagnostic is an annualized mathematical extrapolation, not a stable expected return.
10. Primary window is longest contiguous common availability block, ties earliest. It is selected before new outcomes, but inherits non-random missingness. Independent OOS remains UNVERIFIED. Registered sensitivities, including failures, are all reported.

[Locked plan](../config/vfs_pre_analysis_plan.yaml) / [first remote design commit](https://github.com/bucheoncityboy/mirae-governance-vfs-research/commit/09a105ce651bc28eaad1e0993b12678a41acf61f).
