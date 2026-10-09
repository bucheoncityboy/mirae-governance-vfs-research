# Data dictionary

| File/column | Definition |
| --- | --- |
| monthly_returns.csv/date | Holding return month, ISO month start |
| VFS / Value / Market | Gross monthly decimal price return; missing is NA |
| spread | VFS minus Value, no RF subtraction |
| common_valid | Both longs and Market have a known return |
| primary_window | Availability-selected contiguous diagnostic block |
| *_reason | OK, missing held return, broken holdings path, or no formation |
| *_traded_weight | Sum of bought and sold weights; initial funding 1; unknown reset NA |
| *_net_10bp / *_net_30bp | Per-one-way-trade cost assumption, decimal net return |
| *_max_weight | Beginning-of-month weight after drift; cap only at formation |
| Mkt-RF / SMB / HML / rf | Conditional reconstructed Korean FF3 factors, monthly decimals |
| performance_summary.csv | Contiguous block summary; CAGR/Sharpe annualized and short-sample diagnostic |
| ff3_alphas.csv | Monthly alpha/t/p/CI; NA when <24 consecutive months |
| formation_summary.csv | Aggregated formation counts and weighted log size/ROE; no security rows |
| coverage_matrix.csv | Original horizon vs available G/BE/returns; firms, not independent time-series N |
| size_G_diagnostics.csv | Cross-sectional proxy/size diagnostic; no causal interpretation |

Original report statistics are isolated in references/original_report_reference_table.csv under REFERENCE_ONLY. OUR_RESULT series never contain MSCI original performance.
