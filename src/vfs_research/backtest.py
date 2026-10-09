import numpy as np
import pandas as pd
from .universe import eligible
from .sorts import classify
from .portfolio import make_weights,step,traded_weight,net_return


def run(p, benchmark, *, formation_month=7, g_quantile=.5, equal_weight=False, exclude_top5=False, stale_days=550, size_neutral=False, kospi_only=False):
    dates=pd.date_range('2016-01-01','2026-04-01',freq='MS');records=[];counts=[];formations=[]
    held={'VFS':None,'Value':None};known={'VFS':True,'Value':True};broken={'VFS':False,'Value':False};funded={'VFS':False,'Value':False}
    f=benchmark.copy()
    if 'Market' not in f:
        # Compatibility with previously archived factor-backed fixtures/diagnostics.
        if not {'Mkt-RF','rf'}.issubset(f):raise ValueError('price benchmark needs Market column')
        f['Market']=f['Mkt-RF']+f.rf
    f=f.set_index('date')
    for date in dates:
        current=p.loc[p.date.eq(date)];trade={s:0. for s in held}
        if date.month==formation_month:
            q=eligible(current)
            q=q.loc[(q.formation_month_end-q.filing_date).dt.days.le(stale_days)]
            if kospi_only:q=q.loc[q.corp_cls_reported.eq('Y')]
            if exclude_top5:
                top=current.nlargest(5,'lag_me').stock_code
                q=q.loc[~q.stock_code.isin(top)]
            q=classify(q,g_quantile,size_neutral)
            target,cells=make_weights(q,equal_weight)
            for cell in ['Low-Good','Low-Bad','High-Good','High-Bad']:
                z=q.loc[q.cell.eq(cell)]
                w=cells.get(cell)
                counts.append({'date':date,'cell':cell,'n':len(z),'cap_feasible':w is not None,'g_tie_fraction':float(z.g_value.eq(z.g_cut_value).mean()) if len(z) else np.nan})
            for s in held:
                target_s=target[s]
                trade[s]=(1. if not funded[s] else traded_weight(target_s,held[s]) if known[s] else np.nan) if target_s is not None else np.nan
                held[s]=target_s;broken[s]=target_s is None;known[s]=target_s is not None
                if target_s is not None:funded[s]=True
                formations.append({'date':date,'strategy':s,'eligible_n':len(q),'held_n':len(target_s) if target_s is not None else 0,'max_formation_weight':float(target_s.max()) if target_s is not None else np.nan,'traded_weight':trade[s],
                                   'weighted_log_ME':float(target_s@np.log(q.set_index('stock_code').loc[target_s.index,'lag_me'])) if target_s is not None else np.nan,
                                   'weighted_ROE':float(target_s@q.set_index('stock_code').loc[target_s.index,'roe']) if target_s is not None else np.nan})
        row={'date':date,'Market':float(f.loc[date,'Market']) if date in f.index else np.nan}
        realized=current.set_index('stock_code')['return']
        for s in held:
            w=held[s];gross=np.nan;reason='no_eligible_annual_formation' if w is None else 'broken_holdings_path'
            if w is not None and not broken[s]:
                try:gross,held[s]=step(w,realized);reason='OK'
                except ValueError as e:broken[s]=True;known[s]=False;reason=str(e)
            row[s]=gross;row[s+'_reason']=reason;row[s+'_n']=len(w) if w is not None else 0
            row[s+'_traded_weight']=trade[s]
            row[s+'_max_weight']=float(w.max()) if w is not None and not broken[s] else np.nan
            row[s+'_weight_sum']=float(w.sum()) if w is not None and not broken[s] else np.nan
            for bps in [10,30]:row[f'{s}_net_{bps}bp']=net_return(gross,trade[s],bps)
        row['spread']=row['VFS']-row['Value'];row['common_valid']=all(np.isfinite(row[s]) for s in ['VFS','Value','Market'])
        records.append(row)
    return pd.DataFrame(records),pd.DataFrame(counts),pd.DataFrame(formations)


def longest_block(d, valid='common_valid'):
    q=d.sort_values('date');best=[];block=[];last=None
    for row in q.itertuples():
        ok=bool(getattr(row,valid))
        if not ok or (last is not None and row.date!=last+pd.offsets.MonthBegin(1)):
            if len(block)>len(best):best=block.copy()
            block=[]
        if ok:block.append(row.date)
        last=row.date
    if len(block)>len(best):best=block
    return best
