import pandas as pd
import pytest
from vfs_research.data_ingest import ROOT
from vfs_research.factors import load_factors
from vfs_research.bias_audit import cost_regression_inputs
from vfs_research.stats import regression


@pytest.mark.parametrize('bps',[10,30])
def test_cost_audit_adds_factor_columns_to_real_price_only_primary(bps):
    # Uses already published aggregate observations, not artificial performance.
    returns=pd.read_csv(ROOT/'outputs/monthly_returns.csv',parse_dates=['date'])
    primary=returns.loc[returns.primary_window].copy()
    assert 'SMB' not in primary
    factors=load_factors(ROOT/'legacy_governance_pilot')
    q=cost_regression_inputs(primary,factors,bps)
    assert q.rf.tolist()==primary.rf.tolist()
    assert {'Mkt-RF','SMB','HML'}.issubset(q)
    assert q.VFS.tolist()==primary[f'VFS_net_{bps}bp'].tolist()
    result=regression(q,'spread')
    assert result['n_months']==6 and result['status']=='NOT_ESTIMATED'
