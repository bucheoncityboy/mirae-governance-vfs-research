from pathlib import Path
from functools import lru_cache
import hashlib,json,os,re
import numpy as np
import pandas as pd
from .pit_features import validate_panel

ROOT=Path(__file__).resolve().parents[2]


def paths():
    legacy=os.environ.get('VFS_LEGACY_ROOT');ff3=os.environ.get('VFS_FF3_ROOT')
    if not legacy or not ff3:raise ValueError('Set VFS_LEGACY_ROOT and VFS_FF3_ROOT to authorized local inputs')
    return Path(legacy).resolve(),Path(ff3).resolve()


def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_benchmark(ff3_root):
    """Price-index benchmark and RF; VFS backtesting needs no SMB/HML inputs."""
    d=pd.read_parquet(Path(ff3_root)/'data/market_excess_return.parquet')
    return d[['date','mkt_return','rf']].rename(columns={'mkt_return':'Market'})


def number(x):
    try:return float(str(x).replace(',','').strip())
    except (ValueError,TypeError):return np.nan


def verify_cached(legacy):
    raw=legacy/'data/raw'
    @lru_cache(maxsize=None)
    def read(h):
        if not re.fullmatch('[a-f0-9]{64}',str(h)):raise ValueError('invalid evidence hash')
        p=raw/(h+'.json')
        if digest(p)!=h:raise ValueError('raw evidence hash mismatch')
        return json.loads(p.read_bytes())
    def filing(hashes,corp,receipt,date):
        hits=[]
        for h in hashes.split('|'):
            hits += [r for r in read(h).get('list',[]) if str(r.get('corp_code'))==str(corp) and str(r.get('rcept_no'))==str(receipt)]
        return len(hits)==1 and pd.to_datetime(hits[0]['rcept_dt'],format='%Y%m%d')==date
    g=pd.read_parquet(legacy/'data/private/governance_pit.parquet')
    valid=[]
    for row in g.itertuples():
        if row.status!='PASS':valid.append(False);continue
        hits=[r for r in read(row.source_hash).get('list',[]) if str(r.get('corp_code'))==str(row.corp_code) and str(r.get('rcept_no'))==str(row.rcept_no)]
        ok=len(hits)==1
        if ok:
            v=hits[0]
            ok=number(v['drctr_co'])==row.total_directors and number(v['otcmp_drctr_co'])==row.outside_directors and row.total_directors>0 and np.isclose(row.g_value,row.outside_directors/row.total_directors) and pd.Timestamp(v['stlm_dt'])==row.period_end and filing(row.filing_list_hash,row.corp_code,row.rcept_no,row.filing_date)
        if not ok:raise ValueError('governance source/date/value verification failed')
        valid.append(ok)
    g=g.loc[valid].copy()
    f=pd.read_parquet(legacy/'data/private/verified_financials.parquet')
    for row in f.itertuples():
        hits=[r for r in read(row.financial_source_hash).get('list',[]) if str(r.get('corp_code'))==str(row.corp_code) and str(r.get('rcept_no'))==str(row.financial_rcept_no) and r.get('fs_div')==row.fs_div and r.get('account_nm')==row.account_nm]
        if not (len(hits)==1 and hits[0].get('currency')=='KRW' and int(hits[0]['bsns_year'])==row.be_year and abs(number(hits[0]['thstrm_amount'])/1e8-row.be_eok)<=max(.011,abs(row.be_eok)*.00001) and filing(row.financial_filing_list_hash,row.corp_code,row.financial_rcept_no,row.financial_filing_date)):
            raise ValueError('financial source/date/value verification failed')
    return g,f,read.cache_info().currsize


def load_panel(verify=True):
    legacy,ff3=paths()
    p=pd.read_parquet(legacy/'data/private/joint_panel.parquet')
    g,f,n=verify_cached(legacy) if verify else (pd.read_parquet(legacy/'data/private/governance_pit.parquet'),pd.read_parquet(legacy/'data/private/verified_financials.parquet'),0)
    q=p.loc[p.joint_eligible].copy()
    keys=['stock_code','rcept_no','source_hash']
    m=q.merge(g[keys+['g_value','filing_date']],on=keys,suffixes=('','_evidence'),how='left',validate='many_to_one')
    if not (np.isclose(m.g_value,m.g_value_evidence).all() and m.filing_date.eq(m.filing_date_evidence).all()):raise ValueError('cached PIT panel G mismatch')
    f=f.copy();f['formation_year']=f.be_year+1
    keys=['stock_code','formation_year','financial_source_hash']
    m=p.merge(f[keys+['be_eok','financial_filing_date']],on=keys,how='left',validate='many_to_one',suffixes=('','_evidence'))
    if not m.loc[m.joint_eligible,'financial_filing_date'].eq(m.loc[m.joint_eligible,'financial_filing_date_evidence']).all():raise ValueError('cached financial filing mismatch')
    # Current-month-cap / verified annual BE rather than stale June PBR for sensitivity timing.
    m['bm_pit']=m.be_eok*100000/m.lag_me
    p=m.drop(columns=['financial_filing_date_evidence'])
    validate_panel(p)
    return p,g,f,{'governance_verified':len(g),'financial_verified':len(f),'raw_objects_rehashed':n,'joint_observations':int(p.joint_eligible.sum()),'joint_companies':int(p.loc[p.joint_eligible].stock_code.nunique()),'source_panel_sha256':digest(legacy/'data/private/joint_panel.parquet'),'market_panel_sha256':digest(ff3/'data/panel_data.parquet'),'live_DART_refresh':'NOT_PERFORMED_NO_API_KEY' if not(os.getenv('DART_API_KEY') or os.getenv('OPENDART_API_KEY')) else 'NOT_REQUIRED_CACHED_SNAPSHOT','current_snapshot_revisions':'as_retrieved_2026-10-09_original_before_correction_unverified'}


def return_audit(ff3):
    raw=pd.read_parquet(ff3/'data/market_data_long.parquet')
    price=raw.loc[raw.item_code.eq('S410000700'),['code','date','value']].sort_values(['code','date'])
    price['unfiltered']=price.groupby('code').value.pct_change(fill_method=None)
    source=pd.read_parquet(ff3/'data/stock_returns.parquet')
    d=source.merge(price,on=['code','date'],validate='one_to_one')
    d['filtered']=d.unfiltered.abs().gt(1)&d['return'].isna()
    d['missing']=d['return'].isna()
    d.groupby('date').agg(filtered_gt100=('filtered','sum'),missing=('missing','sum'),rows=('code','size')).to_csv(ROOT/'outputs/return_filter_audit.csv')
    good=d['return'].notna()&d.unfiltered.notna()
    return {'filtered_gt100_count':int(d.filtered.sum()),'price_arithmetic_max_error':float((d.loc[good,'return']-d.loc[good,'unfiltered']).abs().max()),'return_basis':'PRICE_RETURN_ONLY','corporate_action_payoffs':'UNVERIFIED','delisting_returns':'UNVERIFIED','cash_dividends':'UNVERIFIED'}
