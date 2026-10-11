"""Three falsifiable VFS theses, kept separate from the locked primary backtest.

Public-only mode uses already verified aggregates. Raw PIT mode computes
within-PBR governance Good/Bad legs from an authorized *local* panel.
It never imputes missing held returns or reports unearned inference.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .backtest import longest_block
from .data_ingest import ROOT
from .portfolio import capped_weights, step
from .sorts import classify
from .universe import eligible
from .pit_features import validate_panel
from .stats import regression

CELLS = ("Low-Good", "Low-Bad", "High-Good", "High-Bad")


def formation_groups(panel, date):
    """One original PIT formation universe, reused by NAV and exploration."""
    base = eligible(panel.loc[panel.date.eq(date)])
    age = (base.formation_month_end - base.filing_date).dt.days
    return classify(base.loc[age.between(0, 550)])


def validate_cell_input(panel):
    required = {"date", "stock_code", "joint_eligible", "bm_pit", "lag_me",
                "g_value", "formation_month_end", "filing_date", "return"}
    if not required.issubset(panel):
        raise ValueError("missing PIT panel columns: " + str(sorted(required - set(panel))))
    p = panel.copy()
    for col in ["date", "formation_month_end", "filing_date", "financial_filing_date", "available_at"]:
        if col in p:
            p[col] = pd.to_datetime(p[col])
    if p.duplicated(["date", "stock_code"]).any():
        raise ValueError("duplicate stock/month")
    if not p.date.dt.is_month_start.all():
        raise ValueError("return dates must be calendar month starts")
    if not p.joint_eligible.isin([True, False]).all():
        raise ValueError("joint_eligible must be boolean")
    q = p.loc[p.joint_eligible]
    for col in ["filing_date", "financial_filing_date", "available_at"]:
        if col in p and not (q[col] <= q.formation_month_end).all():
            raise ValueError("future disclosure")
    if not (q.formation_month_end < q.date).all():
        raise ValueError("same-month return leakage")
    return p


def cell_monthly(panel):
    """Use original June information/July formation and independent annual paths.

    A missing held return invalidates only that cell through the next formation;
    it is never treated as zero or removed ex post.
    """
    p = validate_cell_input(panel)
    holdings = {c: None for c in CELLS}
    broken = {c: True for c in CELLS}
    rows = []
    for date in pd.date_range("2016-01-01", "2026-04-01", freq="MS"):
        current = p.loc[p.date.eq(date)]
        if date.month == 7:
            base = formation_groups(p, date)
            for cell in CELLS:
                z = base.loc[base.cell.eq(cell)]
                try:
                    holdings[cell] = capped_weights(z.set_index("stock_code").lag_me)
                except ValueError:
                    holdings[cell] = None
                broken[cell] = holdings[cell] is None
        realized = current.set_index("stock_code")["return"]
        record = {"date": date}
        for cell in CELLS:
            w = holdings[cell]
            result = np.nan
            record[cell + "_held_n"] = len(w) if w is not None else 0
            record[cell + "_missing_held_n"] = int(realized.reindex(w.index).isna().sum()) if w is not None and not broken[cell] else 0
            record[cell + "_missing_weight"] = float(w.loc[realized.reindex(w.index).isna()].sum()) if w is not None and not broken[cell] else 0.
            reason = "NO_VALID_FORMATION" if w is None else "BROKEN_ANNUAL_PATH"
            if w is not None and not broken[cell]:
                try:
                    result, holdings[cell] = step(w, realized)
                    reason = "OK"
                except ValueError as exc:
                    broken[cell] = True
                    reason = str(exc)
            record[cell] = result
            record[cell + "_status"] = reason
        rows.append(record)
    return pd.DataFrame(rows)


def paired_description(frame, good, bad):
    d = frame[["date", good, bad]].copy().sort_values("date")
    if d.date.duplicated().any():
        raise ValueError("duplicate pair/month")
    d["common_valid"] = np.isfinite(d[good]) & np.isfinite(d[bad])
    dates = longest_block(d)
    observed = d.loc[d.date.isin(dates)]
    if not len(observed):
        return {"status": "NOT_ESTIMATED_NO_CONTIGUOUS_PAIR", "months": 0,
                "inference": "NOT_ESTIMATED", "return_basis": "PRICE_RETURN_ONLY"}
    spread = observed[good] - observed[bad]
    return {"status": "DESCRIPTIVE_ONLY", "months": int(len(observed)),
            "start": dates[0].strftime("%Y-%m"), "end": dates[-1].strftime("%Y-%m"),
            "mean_monthly_good_minus_bad_pp": float(100 * spread.mean()),
            "positive_spread_months": int(spread.gt(0).sum()),
            "negative_spread_months": int(spread.lt(0).sum()),
            "paired_valid_months_all_blocks": int(d.common_valid.sum()),
            "good_cumulative_pct": float(100 * ((1 + observed[good]).prod() - 1)),
            "bad_cumulative_pct": float(100 * ((1 + observed[bad]).prod() - 1)),
            "inference": "NOT_ESTIMATED",
            "note": "Post-baseline exploratory comparison. No independent OOS or causal claim.",
            "return_basis": "PRICE_RETURN_ONLY"}


def public_results(root=ROOT):
    root = Path(root)
    d = pd.read_csv(root / "outputs/monthly_returns.csv", parse_dates=["date"])
    paired = paired_description(d, "VFS", "Value")
    own = d[["date", "VFS", "Market"]].copy()
    own["common_valid"] = own.VFS.notna() & own.Market.notna()
    own_dates = longest_block(own)
    own = own.loc[own.date.isin(own_dates)]
    neutral = pd.read_csv(root / "outputs/reconstruction/exploratory_g_neutral_monthly.csv",
                          parse_dates=["date"])
    g_comp = paired_description(neutral, "VFS", "GNeutral")
    robustness = pd.read_csv(root / "outputs/robustness.csv")
    ew = robustness.loc[robustness.spec_id.eq("equal_weight")]
    size = pd.read_csv(root / "outputs/size_G_diagnostics.csv")
    result = {
        "scope": "CORE_THESIS_EXPLORATORY_POST_BASELINE",
        "original_vfs_results_modified": False,
        "H1_low_pbr_governance": {"status": "NEEDS_AUTHORIZED_PIT_CELL_RETURNS",
                                  "method": "Low-Good minus Low-Bad; matched annual formation"},
        "H2_high_pbr_governance": {"status": "NEEDS_AUTHORIZED_PIT_CELL_RETURNS",
                                   "method": "High-Good minus High-Bad; matched annual formation"},
        "H3_strategy": {"status": "SHORT_WINDOW_DESCRIPTIVE_ONLY",
                         "vfs_minus_value": paired,
                         "vfs_minus_g_neutral": g_comp,
                         "vfs_own_months": int(len(own)),
                         "vfs_own_total_return_pct": float(100 * ((1 + own.VFS).prod() - 1)) if len(own) else None,
                         "equal_weight_vfs_minus_value_monthly_pp": float(100 * ew.iloc[0].primary_window_mean_spread) if len(ew) else None},
        "confounding": {
            "G_log_ME_correlation_min": float(size.G_log_ME_correlation.min()),
            "G_log_ME_correlation_max": float(size.G_log_ME_correlation.max())},
        "limitations": ["MSCI governance score not available; outside-director proxy only",
                        "PBR/style/size/weighting differences mean VFS-Value is not pure G alpha",
                        "Cash dividends, corporate-action payoff, delisting, OOS unverified",
                        "No significance claim from six or two continuous months"] }
    return result


def cell_segments(cells):
    """Every continuous block, keeping gaps visible; never concatenate NAV."""
    rows = []
    for label, legs in [(c, [c]) for c in CELLS] + [("H1", list(CELLS[:2])), ("H2", list(CELLS[2:]))]:
        q = cells[["date"] + legs].copy()
        q["valid"] = np.isfinite(q[legs]).all(axis=1)
        q["block"] = (~q.valid | q.date.diff().dt.days.gt(32)).cumsum()
        for _, z in q.loc[q.valid].groupby("block"):
            rows.append({"series": label, "start": z.date.min(), "end": z.date.max(), "months": len(z)})
    return pd.DataFrame(rows)


def formation_diagnostics(panel):
    rows = []
    for date in pd.date_range("2016-07-01", "2025-07-01", freq="12MS"):
        q = formation_groups(panel, date)
        for cell in CELLS:
            z = q.loc[q.cell.eq(cell)].set_index("stock_code")
            try:
                w = capped_weights(z.lag_me)
            except ValueError:
                w = None
            row = {"date": date, "cell": cell, "n": len(z), "cap_feasible": w is not None,
                   "max_weight": float(w.max()) if w is not None else np.nan,
                   "hhi": float((w**2).sum()) if w is not None else np.nan,
                   "effective_n": float(1/(w**2).sum()) if w is not None else np.nan}
            for feature in ["pbr", "lag_me", "g_value", "roe", "leverage"]:
                a = pd.to_numeric(z[feature], errors="coerce") if feature in z else pd.Series(np.nan, index=z.index)
                valid = np.isfinite(a)
                row[feature + "_observed_n"] = int(valid.sum())
                for suffix, func in [("mean", "mean"), ("median", "median")]:
                    row[feature + "_" + suffix] = float(getattr(a.loc[valid], func)()) if valid.any() else np.nan
                for quantile in [.1, .9]:
                    row[feature + f"_q{int(100*quantile)}"] = float(a.loc[valid].quantile(quantile)) if valid.any() else np.nan
                coverage = float(w.loc[valid].sum()) if w is not None else np.nan
                row[feature + "_weight_coverage"] = coverage
                row[feature + "_weighted_observed_mean"] = float(w.loc[valid] @ a.loc[valid] / coverage) if coverage > 0 else np.nan
            rows.append(row)
    return pd.DataFrame(rows)


def infer_pairs(cells, factors):
    """Original 24-month gate, all leg/spread HAC3/6 tests in one Holm family."""
    rows = []
    for hypothesis, good, bad in [("H1", *CELLS[:2]), ("H2", *CELLS[2:])]:
        z = cells[["date", good, bad]].copy()
        z["common_valid"] = np.isfinite(z[[good, bad]]).all(axis=1)
        dates = longest_block(z)
        q = z.loc[z.date.isin(dates)].merge(factors, on="date", how="left", validate="one_to_one")
        q["spread"] = q[good] - q[bad]
        for lag in [3, 6]:
            for strategy in [good, bad, "spread"]:
                row = regression(q, strategy, hac=lag)
                row.update(hypothesis=hypothesis, model="FF3", pair_months=len(q))
                rows.append(row)
            row = regression(q, "spread", hac=lag, mean_only=True)
            row.update(hypothesis=hypothesis, model="MEAN_SPREAD", pair_months=len(q))
            rows.append(row)
    d = pd.DataFrame(rows)
    d["p_holm"] = np.nan
    valid = d.p_hac.notna()
    if valid.any():
        from statsmodels.stats.multitest import multipletests
        d.loc[valid, "p_holm"] = multipletests(d.loc[valid, "p_hac"], method="holm")[1]
    d["multiplicity_family"] = "CORE_CELL_16_HAC_SPECIFICATIONS_EXPLORATORY"
    return d


def write_results(value, target):
    def clean(x):
        if isinstance(x, dict): return {k: clean(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)): return [clean(v) for v in x]
        if isinstance(x, (np.floating, float)) and not np.isfinite(x): return None
        if isinstance(x, np.generic): return x.item()
        return x
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(clean(value), ensure_ascii=False, allow_nan=False, indent=2) + "\n")


def empirical_run(panel, out, evidence=None, root=ROOT):
    """Write only approved aggregate data; no securities or holdings exported."""
    from .core_cross_section import explore
    from .backtest import run
    out, root = Path(out), Path(root)
    out.mkdir(parents=True, exist_ok=True)
    panel = validate_cell_input(panel)
    cells = cell_monthly(panel)
    formation = formation_diagnostics(panel)
    factors = pd.read_csv(root / "outputs/factor_test_inputs.csv", parse_dates=["date"])[["date", "rf", "Mkt-RF", "SMB", "HML"]]
    inference = infer_pairs(cells, factors)
    result = public_results(root)
    result["source_validation"] = evidence or {"status": "PIT_VALIDATED_SOURCE_NOT_REHASHED"}
    if evidence:
        result["source_validation"]["live_DART_refresh"] = "NOT_PERFORMED_OFFLINE_CACHED_EVIDENCE"
        result["source_validation"]["current_snapshot_revisions"] = "CURRENT_OFFICIAL_RESPONSES_ORIGINAL_BEFORE_CORRECTION_UNVERIFIED"
        result["source_validation"]["status"] = "RAW_HASH_RECEIPT_DATE_AND_VALUE_REVERIFIED"
    result["analysis_plan_sha256"] = hashlib.sha256((root/'config/core_hypotheses_exploratory_plan.yaml').read_bytes()).hexdigest()
    result["analysis_plan_role"] = "POST_BASELINE_EXPLORATORY_NOT_PREREGISTERED"
    result["source_validation"]["private_paths_published"] = False
    result["hypothesis_results"] = []
    for name, key, good, bad in [("H1", "H1_low_pbr_governance", *CELLS[:2]), ("H2", "H2_high_pbr_governance", *CELLS[2:])]:
        r = paired_description(cells, good, bad)
        estimated = inference.loc[inference.hypothesis.eq(name) & inference.model.eq('FF3') & inference.strategy.eq('spread')]
        judgment = "INSUFFICIENT_EVIDENCE"
        if len(estimated) and estimated.status.ne('NOT_ESTIMATED').all():
            r['inference'] = 'ESTIMATED_EXPLORATORY'
            if estimated.alpha.gt(0).all() and estimated.p_holm.lt(.05).all():
                judgment = 'SUPPORTED_WITH_LIMITATIONS'
            elif estimated.alpha.lt(0).all() or estimated.p_holm.ge(.05).all():
                judgment = 'NOT_SUPPORTED_IN_OBSERVED_SAMPLE'
            else:
                judgment = 'MIXED_EVIDENCE'
        z = formation.loc[formation.cell.isin([good, bad]) & formation.date.between(r.get("start", "1900-01"), r.get("end", "1900-01"))]
        r.update(judgment=judgment, hypothesis=name, good=good, bad=bad,
                 formation_companies_by_cell={c: int(z.loc[z.cell.eq(c), "n"].sum()) for c in [good,bad]},
                 matched_held_security_months={c: int(cells.loc[cells.date.between(r.get("start", "1900-01"), r.get("end", "1900-01")), c+"_held_n"].sum()) for c in [good,bad]},
                 claim="Return-based exploratory comparison; value-trap/premium causal interpretation unverified")
        result[key] = r
        result["hypothesis_results"].append(r)
    h3 = result["H3_strategy"]
    h3.update(hypothesis="H3", judgment="MIXED_EVIDENCE", inference="NOT_ESTIMATED")
    result["hypothesis_results"].append(h3)
    cross = explore(panel, out)
    result["cross_section"] = cross
    baseline = pd.read_csv(root / "outputs/monthly_returns.csv", parse_dates=["date"])
    replay, _, _ = run(panel, baseline[["date", "Market"]])
    merged = baseline.merge(replay, on="date", suffixes=("_old", "_new"), validate="one_to_one")
    errors = {s: int((~np.isclose(merged[s+"_old"], merged[s+"_new"], atol=1e-12, rtol=0, equal_nan=True)).sum()) for s in ["VFS", "Value", "Market"]}
    if any(errors.values()):
        raise ValueError("baseline monthly return drift: " + str(errors))
    result["baseline_invariance"] = {"changed_monthly_returns_above_1e_12": errors, "primary_design_modified": False}
    cells.to_csv(out / "cell_monthly_returns.csv", index=False)
    formation.to_csv(out / "formation_diagnostics.csv", index=False)
    cell_segments(cells).to_csv(out / "cell_continuous_segments.csv", index=False)
    inference.to_csv(out / "cell_inference.csv", index=False)
    pd.DataFrame([{k:v for k,v in r.items() if not isinstance(v,(dict,list))} for r in result["hypothesis_results"]]).to_csv(out / "hypothesis_judgments.csv", index=False)
    write_results(result, out / "hypothesis_results.json")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Core VFS research hypotheses, not a design replacement")
    parser.add_argument("--private-panel", type=Path,
                        help="Authorized verified PIT parquet, not part of the public repo")
    parser.add_argument("--verified-local", action="store_true", help="Rehash authorized cached G/financial evidence via original loader; publish aggregates only")
    parser.add_argument("--out", type=Path, help="Write aggregated JSON; raw-mode path must be outside repository")
    args = parser.parse_args(argv)
    if args.verified_local:
        if args.private_panel is not None:
            parser.error("choose --verified-local or --private-panel")
        from .data_ingest import load_panel
        panel, _, _, evidence = load_panel(verify=True)
        validate_panel(panel)
        empirical_run(panel, args.out or ROOT / "outputs/core_hypotheses", evidence)
        print("CORE_HYPOTHESES_AGGREGATE_EMPIRICAL_RUN_COMPLETE")
        return
    result = public_results()
    published = ROOT / 'outputs/core_hypotheses/hypothesis_results.json'
    if args.private_panel is None and published.exists():
        result = json.loads(published.read_text())
        cells = pd.read_csv(published.with_name('cell_monthly_returns.csv'), parse_dates=['date'])
        for key,good,bad in [('H1_low_pbr_governance',*CELLS[:2]),('H2_high_pbr_governance',*CELLS[2:])]:
            actual=paired_description(cells,good,bad)
            for field in ['months','start','end','mean_monthly_good_minus_bad_pp','good_cumulative_pct','bad_cumulative_pct']:
                if isinstance(actual[field],float):
                    if not np.isclose(actual[field],result[key][field],atol=1e-12,rtol=0):raise ValueError('published cell arithmetic mismatch')
                elif actual[field]!=result[key][field]:raise ValueError('published cell window mismatch')
        result['execution_mode']='PUBLIC_AGGREGATES_RECALCULATED_SOURCE_NOT_ACCESSED'
    if args.private_panel is not None:
        if args.out is None:
            parser.error("--out is mandatory for private empirical analysis")
        target = args.out.resolve()
        if target == ROOT or ROOT in target.parents:
            parser.error("private empirical analysis output must be outside the public repository")
        panel = pd.read_parquet(args.private_panel)
        validate_panel(panel)
        cells = cell_monthly(panel)
        result["H1_low_pbr_governance"] = paired_description(cells, "Low-Good", "Low-Bad")
        result["H2_high_pbr_governance"] = paired_description(cells, "High-Good", "High-Bad")
        result["private_mode"] = "AUTHORIZED_RAW_INPUT_EXPLORATORY_NOT_PUBLISHED"
    output = json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output)
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
