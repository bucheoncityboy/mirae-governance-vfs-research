"""Observed annual-membership panels: exploratory, never investable NAV.

Security rows stay in memory. Only group aggregates are exported. Repeated
firms and five formation cohorts are explicitly not independent observations.
"""
import numpy as np
import pandas as pd

from .core_hypotheses import CELLS, formation_groups


def annual_membership(panel):
    rows = []
    for date in pd.date_range("2016-07-01", "2025-07-01", freq="12MS"):
        q = formation_groups(panel, date)
        if q.empty:
            continue
        q["size_stratum"] = ""
        for _, z in q.groupby("pbr_group"):
            a, b = z.lag_me.quantile([1/3, 2/3])
            q.loc[z.index, "size_stratum"] = np.select([z.lag_me.le(a), z.lag_me.le(b)], ["Small", "Middle"], default="Large")
        q["roe"] = q["roe"] if "roe" in q else np.nan
        q["roe_stratum"] = np.select([q.roe.isna(), q.roe.le(0)], ["Missing", "Nonpositive"], default="Positive")
        q["cohort"] = date.year
        q["formation_date"] = date
        rows.append(q[["stock_code", "cohort", "formation_date", "cell", "pbr_group", "lag_me", "pbr", "roe", "size_stratum", "roe_stratum"]])
    columns = ["stock_code", "cohort", "formation_date", "cell", "pbr_group", "lag_me", "pbr", "roe", "size_stratum", "roe_stratum"]
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=columns)


def monthly_membership(panel, members):
    rows = []
    for (cohort, formation), q in members.groupby(["cohort", "formation_date"]):
        dates = pd.date_range(formation, min(formation + pd.DateOffset(months=11), pd.Timestamp("2026-04-01")), freq="MS")
        z = q.merge(pd.DataFrame({"date": dates}), how="cross")
        rows.append(z)
    cols = list(members) + ["date", "return"]
    if not rows:
        return pd.DataFrame(columns=cols)
    z = pd.concat(rows, ignore_index=True).merge(panel[["stock_code", "date", "return"]], on=["stock_code", "date"], how="left", validate="many_to_one")
    z["observed"] = np.isfinite(z["return"]) & z["return"].ge(-1)
    z.loc[~z.observed, "return"] = np.nan
    return z


def grouped_monthly(z, stratum=None):
    keys = ["date", "cohort", "cell"] + ([stratum] if stratum else [])
    rows = []
    for key, q in z.groupby(keys, observed=True):
        row = dict(zip(keys, key))
        valid = q.observed
        row.update(expected_n=len(q), observed_n=int(valid.sum()), missing_n=int((~valid).sum()),
                   missing_fraction=float((~valid).mean()), observed_return_mean=q.loc[valid, "return"].mean(),
                   loss_20pct_fraction=float(q.loc[valid, "return"].le(-.2).mean()) if valid.any() else np.nan)
        rows.append(row)
    return pd.DataFrame(rows)


def paired_monthly(aggregate, stratum=None):
    rows = []
    keys = ["date", "cohort"] + ([stratum] if stratum else [])
    for key, q in aggregate.groupby(keys, observed=True):
        q = q.set_index("cell")
        for group in ["Low", "High"]:
            good, bad = group + "-Good", group + "-Bad"
            if good not in q.index or bad not in q.index:
                continue
            g, b = q.loc[good], q.loc[bad]
            row = dict(zip(keys, key))
            row.update(pbr_group=group, good_observed_n=int(g.observed_n), bad_observed_n=int(b.observed_n),
                       good_mean=g.observed_return_mean, bad_mean=b.observed_return_mean,
                       good_minus_bad=g.observed_return_mean-b.observed_return_mean,
                       missing_fraction_good=g.missing_fraction, missing_fraction_bad=b.missing_fraction)
            rows.append(row)
    return pd.DataFrame(rows)


def forward_loss(panel, members):
    """12 formation-forward price months, requiring every month; no delisting fill."""
    returns = panel.pivot(index="stock_code", columns="date", values="return")
    details = []
    for (cohort, formation, cell), q in members.groupby(["cohort", "formation_date", "cell"]):
        dates = pd.date_range(formation, periods=12, freq="MS")
        history = returns.reindex(index=q.stock_code, columns=dates)
        complete = (np.isfinite(history) & history.ge(-1)).all(axis=1)
        right_censored = dates[-1] > min(panel.date.max(), pd.Timestamp("2026-04-01"))
        if right_censored:
            complete[:] = False
        realized = (1 + history.loc[complete]).prod(axis=1) - 1
        details.append({"cohort": cohort, "cell": cell, "formation_n": len(q), "complete_12m_n": int(complete.sum()),
                        "right_censored_n": len(q) if right_censored else 0,
                        "missing_or_invalid_path_n": int((~complete).sum()) if not right_censored else 0,
                        "loss_30pct_n": int(realized.le(-.3).sum()),
                        "loss_30pct_fraction_complete": float(realized.le(-.3).mean()) if len(realized) else np.nan,
                        "mean_forward_price_return_complete": float(realized.mean()) if len(realized) else np.nan,
                        "role": "EXPLORATORY_SELECTED_COMPLETE_SECURITY_PATHS_NOT_NAV"})
    return pd.DataFrame(details)


def cluster_model(z, minimum_cohorts=10):
    """Two-way firm / annual-formation clusters; suppress unreliable small-G tests."""
    rows = []
    for group, q in z.groupby("pbr_group"):
        q = q.loc[q.observed & np.isfinite(q.roe) & np.isfinite(q.pbr)].copy()
        n_firms, n_cohorts, n_months = q.stock_code.nunique(), q.cohort.nunique(), q.date.nunique()
        row = {"pbr_group": group, "security_months": len(q), "firms": n_firms,
               "months": n_months, "formation_cohorts": n_cohorts,
               "model": "MONTH_FE_GOOD_LOG_ME_PBR_PIT_ROE_TWO_WAY_FIRM_COHORT",
               "status": "NOT_ESTIMATED", "reason": "fewer_than_10_annual_formation_clusters",
               "good_coefficient": np.nan, "p_cluster": np.nan, "ci_low": np.nan, "ci_high": np.nan}
        if n_cohorts >= minimum_cohorts and n_firms >= 30 and n_months >= 24:
            import statsmodels.formula.api as smf
            from scipy.stats import t
            q["good"] = q.cell.str.endswith("-Good").astype(int)
            q["log_me"] = np.log(q.lag_me)
            q["month_fe"] = q.date.dt.strftime("%Y-%m")
            groups = np.column_stack([pd.factorize(q.stock_code)[0], pd.factorize(q.cohort)[0]])
            m = smf.ols('Q("return") ~ good + log_me + pbr + roe + C(month_fe)', data=q).fit(cov_type="cluster", cov_kwds={"groups": groups, "use_correction": True}, use_t=True)
            beta, se = m.params["good"], m.bse["good"]
            if np.isfinite(se) and se > 0:
                df = min(n_firms, n_cohorts) - 1
                row.update(status="ESTIMATED_EXPLORATORY", reason="", good_coefficient=beta,
                           p_cluster=2*t.sf(abs(beta/se), df), ci_low=beta-t.ppf(.975,df)*se, ci_high=beta+t.ppf(.975,df)*se)
        rows.append(row)
    d = pd.DataFrame(rows)
    d["p_holm"] = np.nan
    tested = d.p_cluster.notna()
    if tested.any():
        from statsmodels.stats.multitest import multipletests
        d.loc[tested, "p_holm"] = multipletests(d.loc[tested, "p_cluster"], method="holm")[1]
    return d


def explore(panel, out):
    members = annual_membership(panel)
    z = monthly_membership(panel, members)
    aggregate = grouped_monthly(z)
    pair = paired_monthly(aggregate)
    aggregate.to_csv(out / "observed_security_monthly.csv", index=False)
    pair.to_csv(out / "observed_good_bad_monthly.csv", index=False)
    for stratum in ["size_stratum", "roe_stratum"]:
        paired_monthly(grouped_monthly(z, stratum), stratum).to_csv(out / ("observed_by_" + stratum + ".csv"), index=False)
    yearly = pair.groupby(["cohort", "pbr_group"]).agg(months=("good_minus_bad", "count"), mean_monthly_difference=("good_minus_bad", "mean"), positive_months=("good_minus_bad", lambda x: int(x.gt(0).sum()))).reset_index()
    yearly.to_csv(out / "observed_by_formation_year.csv", index=False)
    losses = forward_loss(panel, members)
    losses.to_csv(out / "forward_loss_12m.csv", index=False)
    model = cluster_model(z)
    model.to_csv(out / "cross_section_inference.csv", index=False)
    summary = {"role": "EXPLORATORY_OBSERVED_RETURNS_NOT_INVESTABLE_NAV", "firms": int(z.stock_code.nunique()),
               "expected_security_months": len(z), "observed_security_months": int(z.observed.sum()),
               "calendar_months": int(z.date.nunique()), "annual_formation_cohorts": int(z.cohort.nunique()),
               "dependence": "Repeated firms/months/cohorts; security-month row count is not independent sample size",
               "selection": "Missing-return firms excluded only from descriptive observed-return moments; selection bias remains",
               "inference": "NOT_ESTIMATED_TOO_FEW_FORMATION_CLUSTERS" if model.status.eq("NOT_ESTIMATED").all() else "EXPLORATORY_CLUSTERED_MODEL",
               "financial_deterioration": "NOT_TESTED_NO_INDEPENDENTLY_VERIFIED_LONGITUDINAL_PROFITABILITY_OUTCOME", "groups": {}}
    summary['forward_loss_price_proxy'] = {}
    for group in ['Low','High']:
        info={}
        for quality in ['Good','Bad']:
            q=losses.loc[losses.cell.eq(group+'-'+quality)]
            n=int(q.complete_12m_n.sum());count=int(q.loss_30pct_n.sum())
            info[quality]={'complete_security_years':n,'loss_security_years':count,'loss_fraction':count/n if n else None,
                           'missing_security_years':int(q.missing_or_invalid_path_n.sum()),'right_censored_security_years':int(q.right_censored_n.sum())}
        wide=losses.loc[losses.cell.str.startswith(group+'-')].pivot(index='cohort',columns='cell',values='loss_30pct_fraction_complete').dropna()
        info['complete_formation_cohorts']=len(wide)
        info['cohorts_good_lower_loss_fraction']=int((wide[group+'-Good']<wide[group+'-Bad']).sum())
        info['role']='DESCRIPTIVE_SELECTED_COMPLETE_PRICE_PATHS_NO_CLUSTER_INFERENCE'
        summary['forward_loss_price_proxy'][group]=info
    for group, q in pair.groupby("pbr_group"):
        summary["groups"][group] = {"months": int(q.good_minus_bad.count()), "mean_monthly_good_minus_bad_pp": float(q.good_minus_bad.mean()*100),
                                      "positive_months": int(q.good_minus_bad.gt(0).sum()), "negative_months": int(q.good_minus_bad.lt(0).sum()),
                                      "mean_missing_fraction_good_pct": float(q.missing_fraction_good.mean()*100), "mean_missing_fraction_bad_pct": float(q.missing_fraction_bad.mean()*100)}
    return summary
