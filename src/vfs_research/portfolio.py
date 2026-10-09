import numpy as np
import pandas as pd


def capped_weights(capital, cap=.25):
    x=pd.Series(capital,dtype=float)
    if x.empty or (~np.isfinite(x)).any() or (x<=0).any() or len(x)*cap<1-1e-12:
        raise ValueError('infeasible cap or invalid capital')
    w=pd.Series(0.,index=x.index);free=x.index
    for _ in range(len(x)+1):
        remaining=1-w.sum()
        proposed=x.loc[free]/x.loc[free].sum()*remaining
        over=proposed>cap+1e-12
        if not over.any():
            w.loc[free]=proposed
            break
        hits=proposed.index[over];w.loc[hits]=cap;free=free.difference(hits)
    if not np.isclose(w.sum(),1) or w.max()>cap+1e-10:
        raise ValueError('cap failed to converge')
    return w


def make_weights(d, equal_weight=False):
    x=d.set_index('stock_code');cells={}
    for cell,z in x.groupby('cell'):
        capital=pd.Series(1.,index=z.index) if equal_weight else z.lag_me
        try:cells[cell]=capped_weights(capital)
        except ValueError:cells[cell]=None
    legs=[cells.get(c) for c in ['Low-Good','High-Good']]
    vfs=pd.concat([.5*z for z in legs]) if all(z is not None for z in legs) else None
    low=x.loc[x.cell.str.startswith('Low-')]
    value=(pd.Series(1.,index=low.index) if equal_weight else low.lag_me)
    value=value/value.sum() if len(value) else None
    return {'VFS':vfs,'Value':value},cells


def traded_weight(target, prior):
    if prior is None:return 1.  # initial funding: buy one portfolio
    idx=target.index.union(prior.index)
    return float((target.reindex(idx,fill_value=0)-prior.reindex(idx,fill_value=0)).abs().sum())


def step(weights, returns):
    r=returns.reindex(weights.index)
    if r.isna().any():raise ValueError('missing held return')
    if (~np.isfinite(r)).any() or (r < -1).any():raise ValueError('invalid held return')
    gross=float(weights@r);nav=1+gross
    if nav<=0:raise ValueError('portfolio exhausted')
    drift=weights*(1+r)/nav
    return gross,drift


def net_return(gross, traded, bps):
    if bps==0:return gross
    return (1-traded*bps/10000)*(1+gross)-1 if np.isfinite(traded) else np.nan
