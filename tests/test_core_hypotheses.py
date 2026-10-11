"""Synthetic mechanics tests, never empirical VFS evidence."""
import numpy as np
import pandas as pd
import pytest
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


def test_direct_entry_rejects_future_pit_and_duplicates():
    p=panel()
    p.loc[0,'filing_date']=p.loc[0,'date']+pd.Timedelta(days=1)
    with pytest.raises(ValueError,match='future disclosure'):cell_monthly(p)
    with pytest.raises(ValueError,match='duplicate'):cell_monthly(pd.concat([panel(),panel().iloc[:1]]))


def test_missing_calendar_month_is_not_joined_and_infinity_not_valid():
    d=pd.DataFrame({'date':pd.to_datetime(['2021-07-01','2021-09-01','2021-10-01','2021-11-01']),
                    'Good':[.1,.02,.03,np.inf],'Bad':[0.,.01,.02,.01]})
    r=paired_description(d,'Good','Bad')
    assert r['months']==2 and r['start']=='2021-09' and r['end']=='2021-10'
    assert r['paired_valid_months_all_blocks']==3


def test_24_month_factor_gate_rf_and_holm_family():
    from vfs_research.core_hypotheses import infer_pairs,CELLS
    rng=np.random.default_rng(1);dates=pd.date_range('2021-07-01',periods=30,freq='MS')
    factors=pd.DataFrame({'date':dates,'rf':.002,'Mkt-RF':rng.normal(0,.03,30),'SMB':rng.normal(0,.02,30),'HML':rng.normal(0,.02,30)})
    cells=pd.DataFrame({'date':dates})
    for i,c in enumerate(CELLS):cells[c]=.004+i*.001+.3*factors['Mkt-RF']+rng.normal(0,.01,30)
    short=infer_pairs(cells.iloc[:23],factors)
    assert short.status.eq('NOT_ESTIMATED').all() and short.alpha.isna().all()
    full=infer_pairs(cells,factors)
    assert len(full)==16 and full.status.eq('ESTIMATED_EXPLORATORY').all()
    assert full.loc[full.strategy.eq('spread'),'rf_subtracted'].eq(False).all()
    assert full.loc[full.strategy.isin(CELLS),'rf_subtracted'].eq(True).all()
    assert full.p_holm.ge(full.p_hac-1e-12).all()


def test_annual_membership_no_monthly_reselection_and_forward_censoring():
    from vfs_research.core_cross_section import annual_membership,monthly_membership,forward_loss,cluster_model
    p=panel();stock='LowGood00'
    p.loc[p.stock_code.eq(stock)&p.date.eq('2021-08-01'),'g_value']=0.
    p.loc[p.stock_code.eq(stock)&p.date.eq('2021-08-01'),'return']=np.nan
    members=annual_membership(p);z=monthly_membership(p,members)
    row=z.loc[z.stock_code.eq(stock)&z.date.eq('2021-08-01')].iloc[0]
    assert row.cell=='Low-Good' and not row.observed
    losses=forward_loss(p,members)
    first=losses.loc[losses.cohort.eq(2021)&losses.cell.eq('Low-Good')].iloc[0]
    assert first.complete_12m_n==11 and first.missing_or_invalid_path_n==1
    last=losses.loc[losses.cohort.eq(2022)]
    assert last.complete_12m_n.eq(0).all() and last.right_censored_n.eq(12).all()
    z['roe']=.05
    inference=cluster_model(z)
    assert inference.formation_cohorts.eq(2).all() and inference.status.eq('NOT_ESTIMATED').all()
    assert inference.good_coefficient.isna().all()


def test_real_cell_aggregate_arithmetic_and_protected_baseline():
    from vfs_research.core_publication import verify
    from vfs_research.data_ingest import digest
    import json
    verify(ROOT)
    r=json.loads((ROOT/'outputs/core_hypotheses/hypothesis_results.json').read_text())
    assert r['source_validation']['source_panel_sha256']==json.loads((ROOT/'outputs/reconstruction/recollected_input_manifest.json').read_text())['files'][0]['sha256']
    assert r['H1_low_pbr_governance']['months']==6 and r['H2_high_pbr_governance']['months']==4
    assert r['cross_section']['forward_loss_price_proxy']['Low']['cohorts_good_lower_loss_fraction']==0
    assert r['baseline_invariance']['changed_monthly_returns_above_1e_12']==dict(VFS=0,Value=0,Market=0)
    assert r['analysis_plan_sha256']==digest(ROOT/'config/core_hypotheses_exploratory_plan.yaml')
