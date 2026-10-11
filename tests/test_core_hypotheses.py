"""Synthetic mechanics tests, never empirical VFS evidence."""
import numpy as np
import pandas as pd
from vfs_research.core_hypotheses import cell_monthly, paired_description, public_results
from vfs_research.data_ingest import ROOT


def panel():
    rows = []
    dates = pd.date_range("2021-07-01", "2022-08-01", freq="MS")
    for d in dates:
        for group in ("Low", "High"):
            for quality in ("Bad", "Good"):
                for i in range(12):
                    code = group + quality + str(i).zfill(2)
                    r = {("Low", "Good"): .03, ("Low", "Bad"): .01,
                         ("High", "Good"): .02, ("High", "Bad"): .01}[(group, quality)]
                    rows.append({"date": d, "stock_code": code, "joint_eligible": True,
                                 "bm_pit": 2.0 if group == "Low" else .2,
                                 "lag_me": 100.0 + i, "g_value": .8 if quality == "Good" else .2,
                                 "formation_month_end": d - pd.Timedelta(days=1),
                                 "filing_date": pd.Timestamp("2021-03-01"), "return": r})
    return pd.DataFrame(rows)


def test_hypotheses_within_same_pbr_sleeve():
    x = cell_monthly(panel())
    low = paired_description(x, "Low-Good", "Low-Bad")
    high = paired_description(x, "High-Good", "High-Bad")
    assert low["months"] == 14 and high["months"] == 14
    assert np.isclose(low["mean_monthly_good_minus_bad_pp"], 2.)
    assert np.isclose(high["mean_monthly_good_minus_bad_pp"], 1.)
    assert low["inference"] == high["inference"] == "NOT_ESTIMATED"


def test_missing_breaks_only_affected_cell_until_next_july():
    p = panel()
    stock = p.loc[(p.date == pd.Timestamp("2021-07-01")) & p.bm_pit.eq(2) &
                  p.g_value.eq(.8), "stock_code"].iloc[0]
    p.loc[p.stock_code.eq(stock) & p.date.eq(pd.Timestamp("2021-08-01")), "return"] = np.nan
    x = cell_monthly(p).set_index("date")
    assert pd.isna(x.loc["2021-08-01", "Low-Good"])
    assert x.loc["2021-09-01":"2022-06-01", "Low-Good"].isna().all()
    assert pd.notna(x.loc["2022-07-01", "Low-Good"])
    assert pd.notna(x.loc["2021-08-01", "Low-Bad"])
    assert paired_description(x.reset_index(), "Low-Good", "Low-Bad")["months"] == 2


def test_public_only_has_no_invented_h1_h2():
    d = public_results(ROOT)
    assert d["H1_low_pbr_governance"]["status"] == "NEEDS_AUTHORIZED_PIT_CELL_RETURNS"
    assert d["H2_high_pbr_governance"]["status"] == "NEEDS_AUTHORIZED_PIT_CELL_RETURNS"
    assert d["H3_strategy"]["vfs_minus_value"]["months"] == 6
    assert d["H3_strategy"]["vfs_minus_g_neutral"]["months"] == 2
    assert d["H3_strategy"]["vfs_own_months"] == 8
    assert d["H3_strategy"]["vfs_minus_value"]["inference"] == "NOT_ESTIMATED"
