"""Synthetic fixtures validate mechanics only; public empirical data are real."""
import json
import numpy as np
import pandas as pd
import pytest
from vfs_research.portfolio import capped_weights,make_weights,step,traded_weight,net_return
from vfs_research.sorts import classify
from vfs_research.pit_features import select_asof,validate_panel
from vfs_research.backtest import run,longest_block
from vfs_research.stats import regression,performance,block_bootstrap_mean
from vfs_research.data_ingest import ROOT


def fixture_panel():
    rows=[]
    for date in pd.date_range('2021-07-01','2022-08-01',freq='MS'):
        for i in range(32):
            rows.append({'date':date,'stock_code':f'{i:06d}','lag_me':100+i*5.,'bm_pit':1/(.3+i*.1),'g_value':(i%8)/8,'joint_eligible':True,'filing_date':pd.Timestamp('2021-03-01'),'financial_filing_date':pd.Timestamp('2021-03-01'),'formation_month_end':date-pd.Timedelta(days=1),'available_at':pd.Timestamp('2021-03-31'),'corp_cls_reported':'Y','return':.01,'roe':.1})
    return pd.DataFrame(rows)


def factor_fixture():
    dates=pd.date_range('2016-01-01','2026-04-01',freq='MS');n=len(dates)
    return pd.DataFrame({'date':dates,'Mkt-RF':np.sin(np.arange(n))*.02,'SMB':np.cos(np.arange(n)*.7)*.01,'HML':np.sin(np.arange(n)*.4)*.01,'rf':.002})


@pytest.mark.parametrize('n',[4,5,10,30,100])
def test_cap_converges_and_preserves_sum(n):
    x=pd.Series(np.geomspace(1,100000,n));w=capped_weights(x)
    assert np.isclose(w.sum(),1) and w.max()<=.25+1e-12


@pytest.mark.parametrize('x',[[],[1,2,3],[1,-2,3,4],[1,2,np.nan,4]])
def test_invalid_cap(x):
    with pytest.raises(ValueError):capped_weights(x)


def test_ties_are_never_randomly_split():
    p=fixture_panel();q=p.loc[p.date.eq(pd.Timestamp('2021-07-01'))].copy();q['bm_pit']=1.;q['g_value']=.5
    z=classify(q)
    assert z.cell.eq('Low-Bad').all()
    w,_=make_weights(z);assert w['VFS'] is None


def test_final_cap_and_both_cells():
    p=fixture_panel();q=classify(p.loc[p.date.eq(pd.Timestamp('2021-07-01'))])
    w,cells=make_weights(q);assert np.isclose(w['VFS'].sum(),1) and w['VFS'].max()<=.125+1e-12
    for name in ['Low-Good','High-Good']:
        assert np.isclose(w['VFS'].reindex(cells[name].index).sum(),.5)


def test_future_observation_insertion_invariance():
    d=pd.DataFrame({'available_at':pd.to_datetime(['2021-03-31']),'filing_date':pd.to_datetime(['2021-03-20']),'period_end':pd.to_datetime(['2020-12-31']),'rcept_no':['1'],'g_value':[.4]})
    future=d.iloc[0].copy();future['available_at']=pd.Timestamp('2022-03-31');future['filing_date']=pd.Timestamp('2022-03-20');future['g_value']=.9
    base=select_asof(d,pd.Timestamp('2021-06-30'))
    changed=select_asof(pd.concat([d,pd.DataFrame([future])]),pd.Timestamp('2021-06-30'))
    assert base.g_value==changed.g_value


def test_late_old_amendment_cannot_replace_new_period():
    d=pd.DataFrame({'available_at':pd.to_datetime(['2021-03-31','2021-05-31']),'filing_date':pd.to_datetime(['2021-03-01','2021-05-01']),'period_end':pd.to_datetime(['2020-12-31','2019-12-31']),'rcept_no':['1','2'],'g_value':[.4,.9]})
    assert select_asof(d,pd.Timestamp('2021-06-30')).g_value==.4


def test_published_after_formation_rejected():
    q=fixture_panel();q.loc[0,'financial_filing_date']=pd.Timestamp('2026-01-01')
    with pytest.raises(ValueError,match='future disclosure'):validate_panel(q)


def test_missing_held_return_is_not_reweighted_or_zero_filled():
    w=pd.Series([.5,.5],index=['a','b']);r=pd.Series([.1,np.nan],index=['a','b'])
    with pytest.raises(ValueError,match='missing held return'):step(w,r)


def test_delisted_company_disappears_from_return_rows():
    w=pd.Series([.5,.5],index=['a','b'])
    with pytest.raises(ValueError):step(w,pd.Series([.1],index=['a']))


def test_weights_drift_under_annual_holding():
    w=pd.Series([.5,.5],index=['a','b']);gross,new=step(w,pd.Series([.2,0],index=['a','b']))
    assert gross==pytest.approx(.1) and new.a==pytest.approx(.6/1.1) and new.sum()==pytest.approx(1)


def test_cost_buy_sell_and_initial_funding():
    a=pd.Series([1.],index=['a']);b=pd.Series([1.],index=['b'])
    assert traded_weight(a,None)==1 and traded_weight(b,a)==2
    assert net_return(.1,2,30)==pytest.approx((1-.006)*1.1-1)
    assert np.isnan(net_return(.1,np.nan,30))
    assert net_return(.1,np.nan,0)==.1


def test_missing_path_cannot_resume_until_annual_reset():
    p=fixture_panel();formation=classify(p.loc[p.date.eq(pd.Timestamp('2021-07-01'))]);weights,_=make_weights(formation);stock=weights['VFS'].index[0]
    p.loc[p.stock_code.eq(stock)&p.date.eq(pd.Timestamp('2021-08-01')),'return']=np.nan
    d,_,_=run(p,factor_fixture())
    assert pd.notna(d.loc[d.date.eq(pd.Timestamp('2021-07-01')),'VFS'].iloc[0])
    assert d.loc[d.date.between('2021-08-01','2022-06-01'),'VFS'].isna().all()
    assert pd.notna(d.loc[d.date.eq(pd.Timestamp('2022-07-01')),'VFS'].iloc[0])
    assert d.loc[d.date.eq(pd.Timestamp('2021-07-01')),'VFS_traded_weight'].iloc[0]==1
    assert np.isnan(d.loc[d.date.eq(pd.Timestamp('2022-07-01')),'VFS_traded_weight'].iloc[0])


def test_no_same_month_return_selection():
    p=fixture_panel();q=p.copy();q['return']=q['return']*20
    _,_,a=run(p,factor_fixture());_,_,b=run(q,factor_fixture())
    # Initial formation must not depend on realized July returns.
    x=a.loc[a.date.eq(pd.Timestamp('2021-07-01'))];y=b.loc[b.date.eq(pd.Timestamp('2021-07-01'))]
    assert np.allclose(x.max_formation_weight,y.max_formation_weight,equal_nan=True)


def test_longest_block_never_joins_missing_calendar_months():
    d=pd.DataFrame({'date':pd.to_datetime(['2021-01-01','2021-02-01','2021-04-01','2021-05-01','2021-06-01']),'common_valid':True})
    assert longest_block(d)==list(pd.to_datetime(['2021-04-01','2021-05-01','2021-06-01']))


def test_less_than_24_months_suppresses_inference():
    d=factor_fixture().iloc[:6].copy();d['VFS']=.01;d['spread']=.003
    a=regression(d,'VFS');assert a['status']=='NOT_ESTIMATED' and np.isnan(a['alpha'])


def test_rf_once_long_zero_spread_and_hac_ci():
    d=factor_fixture().iloc[:40].copy();signal=.003+.2*d['Mkt-RF']+.1*d.SMB-.1*d.HML+np.sin(np.arange(len(d))*1.7)*.002
    d['VFS']=signal+d.rf;d['spread']=signal
    long=regression(d,'VFS');spread=regression(d,'spread')
    assert long['alpha']==pytest.approx(spread['alpha'])
    assert long['rf_subtracted'] and not spread['rf_subtracted']
    assert spread['ci_low']<spread['alpha']<spread['ci_high'] and 0<=spread['p_hac']<=1


def test_regression_gaps_cannot_be_hidden():
    d=factor_fixture().iloc[:40].drop(index=12).copy();d['VFS']=.01
    assert regression(d,'VFS')['status']=='NOT_ESTIMATED'


def test_first_month_loss_included_in_mdd():
    d=factor_fixture().iloc[:2].copy();d['VFS']=[-.1,.02]
    assert performance(d,'VFS')['mdd']==pytest.approx(-.1)


def test_short_block_bootstrap_is_not_estimated():
    assert block_bootstrap_mean([.01]*6,6)['status']=='NOT_ESTIMATED'


def test_price_only_label_and_no_synthetic_evidence():
    s=json.loads((ROOT/'outputs/results_status.json').read_text());assert s['return_basis']=='PRICE_RETURN_ONLY'
    gate=json.loads((ROOT/'outputs/gate_a.json').read_text());assert gate['raw_objects_rehashed']>0 and gate['price_arithmetic_max_error']==0
    assert gate['filtered_gt100_count']==659


def test_public_consistency():
    from vfs_research.reporting import verify_public
    verify_public()


def test_private_raw_ignored():
    text=(ROOT/'.gitignore').read_text();assert 'data/private/' in text and 'data/raw/' in text and '.env' in text


def test_original_ff3_120_hashes_unchanged():
    d=pd.read_csv(ROOT/'docs/original_ff3_integrity.csv')
    assert len(d)==120 and d.unchanged.all() and d.baseline_sha256.eq(d.current_sha256).all()


def test_momentum_excludes_recent_and_future_returns():
    from vfs_research.control_diagnostics import price_momentum_asof
    dates=pd.date_range('2020-07-01','2021-08-01',freq='MS')
    p=pd.DataFrame({'date':dates,'stock_code':'a','return':.01})
    expected=(1.01**11)-1
    assert price_momentum_asof(p,'2021-07-01').loc['a']==pytest.approx(expected)
    p.loc[p.date.ge(pd.Timestamp('2021-06-01')),'return']=9.
    assert price_momentum_asof(p,'2021-07-01').loc['a']==pytest.approx(expected)


def test_momentum_missing_past_month_stays_unknown():
    from vfs_research.control_diagnostics import price_momentum_asof
    p=pd.DataFrame({'date':pd.date_range('2020-07-01','2021-05-01',freq='MS'),'stock_code':'a','return':.01}).drop(index=4)
    assert pd.isna(price_momentum_asof(p,'2021-07-01').loc['a'])


def test_vfs_backtest_needs_no_ff3_factors():
    p=fixture_panel();f=factor_fixture();benchmark=f[['date','rf']].copy();benchmark['Market']=f['Mkt-RF']+f.rf
    direct,_,_=run(p,benchmark);archived,_,_=run(p,f)
    for name in ['VFS','Value','Market']:
        assert np.allclose(direct[name],archived[name],equal_nan=True)


def test_value_missing_month_does_not_shorten_vfs_own_diagnostic():
    from vfs_research.strategy_diagnostics import vfs_observed_window
    dates=pd.date_range('2021-07-01',periods=8,freq='MS')
    d=pd.DataFrame({'date':dates,'VFS':.01,'Market':.005,'Value':[.01]*6+[np.nan]*2})
    assert len(vfs_observed_window(d))==8


def test_vfs_own_diagnostic_never_bridges_missing_month():
    from vfs_research.strategy_diagnostics import vfs_observed_window
    dates=pd.date_range('2021-07-01',periods=8,freq='MS')
    d=pd.DataFrame({'date':dates,'VFS':[.01]*3+[np.nan]+[.01]*4,'Market':.005})
    assert len(vfs_observed_window(d))==4
