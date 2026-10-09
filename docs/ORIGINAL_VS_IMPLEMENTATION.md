# Original versus implementation - GATE B

| Item | Classification | Original | Independent implementation |
| --- | --- | --- | --- |
| PBR × G four cells | Explicit p20 table 6 | Good vs Bad, Low vs High | Same economic rule; different G proxy |
| Governance | Explicit p20/p27 | MSCI score, several governance dimensions | Outside / total directors, public disclosure proxy |
| Long allocation | Explicit p21 | Low-Good and High-Good 1:1 | 50% + 50% at annual formation |
| Cap | Explicit p21, timing unspecified | 25% per cell; 12.5% overall | Convergent redistribution at formation, drift disclosed |
| Rebalance | Explicit p21 figure footnotes | Annual | June information, July return start: our assumption |
| PBR/G threshold | Not explicit | Numeric cutoffs unreported | Cross-sectional PBR median; within-group G median; ties fixed |
| Return | Explicit p21 | Includes cash dividends | PRICE_RETURN_ONLY; no performance-equivalence claim |
| Winsorization | Explicit operation, unspecified quantile | Winsorized | No additional clipping; inherited filter is unresolved |
| Value comparator | Explicit p21, universe details unavailable | Market-cap weighted Value | Same eligibility set Low-PBR, uncapped |
| Market | Explicit p21 | KOSPI | KOSPI price series; same common diagnostic months |
| Financial scope | Not explicit enough for public PIT reproduction | FnGuide | Account/currency/filing matched annual BE; revision vintage caveat |
| FF3/HAC / spread | Our extension | Not given in table 7 | Implemented estimator; six months => NOT_ESTIMATED |
| COE/causal reform test | Original p10-16/p26-27 | Valuation model and governance risk | CONTEXT_ONLY / NOT_TESTED |
| Sector and semiconductor attribution | Inference possible, empirical inputs missing | p22-23 stock/style discussion | NOT_TESTED historical sector; size/ROE diagnostic only |
| OOS / PIT / bias tests | Our extension | Original complete audit not provided | No independent OOS; bias audit explicitly unresolved |

Original report verified from the official 30-page PDF on 2026-10-10. Printed page numbers equal PDF page index + 1. The PDF is not republished. [Assumptions](ASSUMPTIONS.md) records all non-original rules.
