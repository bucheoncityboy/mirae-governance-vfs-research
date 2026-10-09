"""PIT price-momentum and ROE coverage, descriptive only; no new strategy selection."""
import numpy as np
import pandas as pd
from .data_ingest import ROOT
from .universe import eligible
from .sorts import classify
from .portfolio import make_weights


def price_momentum_asof(p,date):
    date=pd.Timestamp(date)
    needed=pd.date_range(date-pd.DateOffset(months=12),date-pd.DateOffset(months=2),freq='MS')
    history=p.loc[p.date.isin(needed)].pivot(index='stock_code',columns='date',values='return').reindex(columns=needed)
    momentum=(1+history).prod(axis=1)-1;momentum.loc[history.isna().any(axis=1)]=np.nan
    return momentum


def build_control_diagnostics():
    p=pd.read_parquet(ROOT/'data/private/pit_panel.parquet');rows=[]
    for date in sorted(p.loc[p.date.dt.month.eq(7)&p.joint_eligible,'date'].unique()):
        date=pd.Timestamp(date);q=classify(eligible(p.loc[p.date.eq(date)]));weights,_=make_weights(q)
        # At July entry, July of prior year through May of current year: skip June.
        momentum=price_momentum_asof(p,date)
        features=q.set_index('stock_code')[['roe','g_value','pbr','lag_me']].copy();features['momentum_12_1_price']=momentum
        for strategy,w in weights.items():
            if w is None:continue
            z=features.reindex(w.index)
            for feature in ['roe','momentum_12_1_price','g_value','pbr']:
                valid=z[feature].notna();coverage=float(w.loc[valid].sum())
                # Conditional observed-feature average is not a return or adjusted-alpha estimate.
                mean=float((w.loc[valid]*z.loc[valid,feature]).sum()/coverage) if coverage>0 else np.nan
                rows.append({'date':date,'strategy':strategy,'feature':feature,'weight_coverage':coverage,'observed_weight_conditional_mean':mean,'complete_weight_mean':mean if np.isclose(coverage,1) else np.nan,'role':'DESCRIPTIVE_CONFOUNDING_ONLY_NOT_CAUSAL_CONTROL','return_basis':'PRICE_RETURN_ONLY' if 'momentum' in feature else 'PIT_DISCLOSURE_FEATURE'})
    pd.DataFrame(rows).to_csv(ROOT/'outputs/control_exposure_diagnostics.csv',index=False)
    print('CONTROL_DIAGNOSTICS',len(rows),'rows; no strategy change or alpha estimates')
