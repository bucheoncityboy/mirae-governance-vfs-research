import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from vfs_research.reconstruction import g_neutral_weights, collect, configure_key, legacy_modules


def test_g_neutral_matches_pbr_budgets_without_selecting_on_g():
    data = pd.DataFrame({'stock_code': [str(i) for i in range(10)],
                         'pbr_group': ['Low'] * 5 + ['High'] * 5,
                         'lag_me': [1, 2, 3, 4, 10, 6, 5, 4, 3, 2],
                         'g_value': np.linspace(0, 1, 10)})
    weights = g_neutral_weights(data)
    assert np.isclose(weights.loc[data.loc[data.pbr_group.eq('Low'), 'stock_code']].sum(), .5)
    assert np.isclose(weights.sum(), 1)
    assert weights.max() <= .125 + 1e-12
    changed = data.assign(g_value=data.g_value.iloc[::-1].to_numpy())
    pd.testing.assert_series_equal(weights, g_neutral_weights(changed))


def test_g_neutral_does_not_relax_infeasible_cap():
    data = pd.DataFrame({'stock_code': ['a', 'b', 'c', 'd', 'e', 'f', 'g'],
                         'pbr_group': ['Low'] * 3 + ['High'] * 4, 'lag_me': 1.})
    with pytest.raises(ValueError, match='infeasible cap'):
        g_neutral_weights(data)


def test_failed_smoke_blocks_collection_before_credentials_or_network(tmp_path):
    (tmp_path / 'smoke_status.json').write_text(json.dumps({'status': 'BLOCKED'}))
    with pytest.raises(ValueError, match='collection refused'):
        collect(tmp_path, tmp_path / 'ff3')


def test_credential_must_be_owner_private(tmp_path):
    path = tmp_path / 'credential'
    path.write_text('0' * 40)
    path.chmod(0o644)
    with pytest.raises(ValueError, match='private'):
        configure_key(path)


def test_adapter_rejects_collection_inside_public_repository():
    from vfs_research.data_ingest import ROOT
    with pytest.raises(ValueError, match='outside both repositories'):
        legacy_modules(ROOT / 'data/private', Path('/unused-source'))
