"""Three falsifiable VFS theses, kept separate from the locked primary backtest.

Public-only mode uses already verified aggregates. Raw PIT mode computes
within-PBR governance Good/Bad legs from an authorized *local* panel.
It never imputes missing held returns or reports unearned inference.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .backtest import longest_block
from .data_ingest import ROOT
from .portfolio import capped_weights, step
from .sorts import classify
from .universe import eligible

CELLS = ("Low-Good", "Low-Bad", "High-Good", "High-Bad")


def cell_monthly(panel):
    """Use original June information/July formation and independent annual paths.

    A missing held return invalidates only that cell through the next formation;
    it is never treated as zero or removed ex post.
    """
    required = {"date", "stock_code", "joint_eligible", "bm_pit", "lag_me",
                "g_value", "formation_month_end", "filing_date", "return"}
    if not required.issubset(panel.columns):
        raise ValueError("missing PIT panel columns: " + str(sorted(required - set(panel.columns))))
    if panel.duplicated(["date", "stock_code"]).any():
        raise ValueError("duplicate stock/month")
    p = panel.copy()
    p["date"] = pd.to_datetime(p.date)
    p["formation_month_end"] = pd.to_datetime(p.formation_month_end)
    p["filing_date"] = pd.to_datetime(p.filing_date)
    holdings = {c: None for c in CELLS}
    broken = {c: True for c in CELLS}
    rows = []
    for date in pd.date_range("2016-01-01", "2026-04-01", freq="MS"):
        current = p.loc[p.date.eq(date)]
        if date.month == 7:
            base = eligible(current)
            age = (base.formation_month_end - base.filing_date).dt.days
            base = classify(base.loc[age.le(550)])
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
    d["common_valid"] = d[good].notna() & d[bad].notna()
    dates = longest_block(d)
    observed = d.loc[d.date.isin(dates)]
    if not len(observed):
        return {"status": "NOT_ESTIMATED_NO_CONTIGUOUS_PAIR", "months": 0,
                "inference": "NOT_ESTIMATED", "return_basis": "PRICE_RETURN_ONLY"}
    spread = observed[good] - observed[bad]
    return {"status": "DESCRIPTIVE_ONLY", "months": int(len(observed)),
            "start": dates[0].strftime("%Y-%m"), "end": dates[-1].strftime("%Y-%m"),
            "mean_monthly_good_minus_bad_pp": float(100 * spread.mean()),
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


def main(argv=None):
    parser = argparse.ArgumentParser(description="Core VFS research hypotheses, not a design replacement")
    parser.add_argument("--private-panel", type=Path,
                        help="Authorized verified PIT parquet, not part of the public repo")
    parser.add_argument("--out", type=Path, help="Write aggregated JSON; raw-mode path must be outside repository")
    args = parser.parse_args(argv)
    result = public_results()
    if args.private_panel is not None:
        if args.out is None:
            parser.error("--out is mandatory for private empirical analysis")
        target = args.out.resolve()
        if target == ROOT or ROOT in target.parents:
            parser.error("private empirical analysis output must be outside the public repository")
        from .pit_features import validate_panel
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
