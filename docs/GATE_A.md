# GATE A - actual input diagnostic

{
  "governance_verified": 4540,
  "financial_verified": 4382,
  "raw_objects_rehashed": 9186,
  "joint_observations": 38742,
  "joint_companies": 782,
  "source_panel_sha256": "c32cac10522ba3971dbda01cb79b68e30ccaa104ab85d08241961d5bbff13d54",
  "market_panel_sha256": "7b7535158649ac6c304a68aedc71a6a301107d75541811aafcdea9380382f584",
  "live_DART_refresh": "NOT_PERFORMED_NO_API_KEY",
  "current_snapshot_revisions": "as_retrieved_2026-10-09_original_before_correction_unverified",
  "filtered_gt100_count": 659,
  "price_arithmetic_max_error": 0.0,
  "return_basis": "PRICE_RETURN_ONLY",
  "corporate_action_payoffs": "UNVERIFIED",
  "delisting_returns": "UNVERIFIED",
  "cash_dividends": "UNVERIFIED",
  "common_valid_months": 8,
  "longest_common_contiguous_months": 6,
  "available_window": [
    "2021-07-01",
    "2021-12-01"
  ],
  "gate_a": "PASS_DIAGNOSTIC_ONLY",
  "investable_total_return_validation": "UNVERIFIED",
  "alpha_feasibility": false,
  "cutoff": "2026-04"
}

The engine has genuine estimable diagnostic months, so limited-result presentation is permitted. A full-period investable backtest is not established. Required historical financial/G evidence is absent before 2021. No missing month is dropped or filled. A missing held return invalidates the annual path until the next formation; future survivors are never selected. The window is selected from availability, not observed returns. Annual holding weights drift between rebalances. Original current-listing selection and correction-vintage risks remain unresolved.

[Access attempts](data_access_probes.json), [coverage](../data_quality/coverage_matrix.csv), [raw snapshot verification](../outputs/gate_a.json). FnGuide row-level data and API responses remain local only. Aggregates are independently authored analysis; provider rights in source data remain unverified.
