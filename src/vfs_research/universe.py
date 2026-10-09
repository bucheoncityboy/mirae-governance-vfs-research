import numpy as np


def eligible(p):
    return p.loc[p.joint_eligible & p.bm_pit.gt(0) & p.lag_me.gt(0) & p.g_value.between(0,1)].copy()


def pbr(p):
    return 1 / p.bm_pit.where(p.bm_pit.gt(0), np.nan)
