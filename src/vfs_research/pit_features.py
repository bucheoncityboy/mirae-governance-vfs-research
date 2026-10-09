import pandas as pd


def select_asof(observations, formation, max_age=550):
    eligible = observations.loc[(observations.available_at <= formation) & (observations.filing_date < formation)]
    if eligible.empty:
        return None
    row = eligible.sort_values(['period_end', 'filing_date', 'rcept_no'], kind='stable').iloc[-1]
    return None if (formation-row.filing_date).days > max_age else row


def validate_panel(p):
    q = p.loc[p.joint_eligible]
    if q.duplicated(['stock_code', 'date']).any():
        raise ValueError('duplicate security-month')
    for col in ['filing_date', 'financial_filing_date', 'available_at']:
        if not (q[col] <= q.formation_month_end).all():
            raise ValueError('future disclosure')
    if not (q.formation_month_end < q.date).all():
        raise ValueError('same-month return leakage')
    return True
