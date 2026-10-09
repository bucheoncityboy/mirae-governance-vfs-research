import pandas as pd


def load_factors(legacy_root,kind='spec_aligned'):
    d=pd.read_csv(legacy_root/'output'/f'ff3_factors_{kind}.csv',parse_dates=['date'])
    return d[['date','Mkt-RF','SMB','HML','rf']]
