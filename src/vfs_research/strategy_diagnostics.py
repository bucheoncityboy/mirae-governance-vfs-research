"""Describe VFS observed paths independently of comparator or factor availability."""
import numpy as np
import pandas as pd
from .data_ingest import ROOT
from .backtest import longest_block
from .stats import performance


def vfs_observed_window(d):
    x=d.copy();x['vfs_valid']=x.VFS.notna()&x.Market.notna()
    dates=longest_block(x,'vfs_valid')
    return x.loc[x.date.isin(dates)].copy()


def vfs_strategy_summary(d):
    q=vfs_observed_window(d)
    return pd.DataFrame([performance(q,s) for s in ['VFS','Market']]) if len(q) else pd.DataFrame()


def export_strategy_diagnostics(d):
    metrics=vfs_strategy_summary(d);metrics.to_csv(ROOT/'outputs/vfs_strategy_summary.csv',index=False)
    q=vfs_observed_window(d)
    q[['date','VFS','Market','rf','VFS_reason','VFS_n']].to_csv(ROOT/'outputs/vfs_observed_path.csv',index=False)
    records=[]
    for strategy in ['VFS','Value','Market']:
        block=[]
        for row in d.sort_values('date').itertuples():
            if pd.notna(getattr(row,strategy)):
                if block and row.date!=block[-1]+pd.offsets.MonthBegin(1):
                    records.append({'strategy':strategy,'start':block[0],'end':block[-1],'n_months':len(block)});block=[]
                block.append(row.date)
            elif block:
                records.append({'strategy':strategy,'start':block[0],'end':block[-1],'n_months':len(block)});block=[]
        if block:records.append({'strategy':strategy,'start':block[0],'end':block[-1],'n_months':len(block)})
    pd.DataFrame(records).to_csv(ROOT/'outputs/observed_segments.csv',index=False)
    return metrics
