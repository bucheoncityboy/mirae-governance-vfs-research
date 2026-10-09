import numpy as np
import pandas as pd
import statsmodels.api as sm


def contiguous(d):
    dates=pd.DatetimeIndex(d.date)
    return len(dates)==len(dates.unique()) and (len(dates)<2 or (dates[1:]==dates[:-1]+pd.offsets.MonthBegin(1)).all())


def regression(d, strategy, hac=3, minimum=24, mean_only=False):
    z=d.dropna(subset=[strategy,'rf','Mkt-RF','SMB','HML']).copy()
    fields={'strategy':strategy,'hac_lags':hac,'n_months':len(z),'status':'NOT_ESTIMATED','reason':'less_than_24_contiguous_months','alpha':np.nan,'t_hac':np.nan,'p_hac':np.nan,'ci_low':np.nan,'ci_high':np.nan,'beta_mkt':np.nan,'beta_smb':np.nan,'beta_hml':np.nan,'rf_subtracted':strategy!='spread' and not mean_only}
    if len(z)<minimum or not contiguous(z):return fields
    y=z[strategy]-(z.rf if fields['rf_subtracted'] else 0)
    X=pd.DataFrame({'const':np.ones(len(z))},index=z.index) if mean_only else sm.add_constant(z[['Mkt-RF','SMB','HML']],has_constant='add')
    m=sm.OLS(y,X).fit(cov_type='HAC',cov_kwds={'maxlags':hac,'use_correction':True},use_t=True)
    ci=m.conf_int().loc['const'];fields.update(status='ESTIMATED_EXPLORATORY',reason='',alpha=m.params['const'],t_hac=m.tvalues['const'],p_hac=m.pvalues['const'],ci_low=ci.iloc[0],ci_high=ci.iloc[1])
    if not mean_only:fields.update(beta_mkt=m.params['Mkt-RF'],beta_smb=m.params.SMB,beta_hml=m.params.HML)
    return fields


def performance(d, strategy):
    r=d[strategy];n=len(r)
    if not n or r.isna().any() or not contiguous(d):raise ValueError('performance requires complete contiguous months')
    nav=np.r_[1.,(1+r).cumprod().to_numpy()];dd=nav/np.maximum.accumulate(nav)-1
    excess=r-d.rf;vol=r.std(ddof=1)*np.sqrt(12)
    downside=np.sqrt(np.mean(np.minimum(excess,0)**2))*np.sqrt(12)
    return {'strategy':strategy,'start':str(d.date.min().date()),'end':str(d.date.max().date()),'n_months':n,'total_return':nav[-1]-1,'cagr':nav[-1]**(12/n)-1,'volatility':vol,
            'sharpe':excess.mean()*12/vol if vol>0 else np.nan,'sortino':excess.mean()*12/downside if downside>0 else np.nan,'mdd':dd.min(),'role':'SHORT_WINDOW_DIAGNOSTIC' if n<24 else 'EXPLORATORY','return_basis':'PRICE_RETURN_ONLY','cost_bps':0}


def block_bootstrap_mean(r, block=6, n_boot=2000, seed=20260528):
    r=np.asarray(r)
    if len(r)<2*block:return {'status':'NOT_ESTIMATED','reason':'insufficient_blocks'}
    rng=np.random.default_rng(seed);idx=np.arange(block);means=[]
    for _ in range(n_boot):
        starts=rng.integers(0,len(r),size=int(np.ceil(len(r)/block)))
        sample=r[((starts[:,None]+idx)%len(r)).ravel()[:len(r)]];means.append(sample.mean())
    lo,hi=np.quantile(means,[.025,.975]);return {'status':'ESTIMATED','ci_low':float(lo),'ci_high':float(hi)}
