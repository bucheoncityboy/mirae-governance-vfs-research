"""Inspect official disclosure candidates around actual held-return gaps.

A matching report title is a lead, never an economic-return correction.
"""
import argparse
import json
from pathlib import Path
import re
import pandas as pd

from .reconstruction import legacy_modules, configure_key, official_api_opener, single_collector, write_json


def inspect_events(workspace, ff3, key_file, output, budget=100):
    workspace, output = Path(workspace).resolve(), Path(output).resolve()
    if not 1 <= budget <= 100:
        raise ValueError('event audit budget must be between 1 and 100')
    configure_key(key_file)
    acquire, _ = legacy_modules(workspace, ff3)
    client = acquire.Client(workspace/'data', budget=budget, interval=.3, opener=official_api_opener)
    prior = pd.read_csv(workspace/'data/api_log_sanitized.csv')
    if len(prior)+budget > 19000:
        raise ValueError('event audit would exceed the recorded session request budget')
    mapping=acquire.load_mapping()
    gaps=pd.read_csv(workspace/'data/private/held_gap_source_diagnosis.csv',dtype={'stock_code':str},parse_dates=['date'])
    keys=gaps[['stock_code','date']].drop_duplicates()
    records=[]; coverage=[]
    terms=re.compile('주식분할|주식병합|합병|분할|상장폐지|감자|자본감소|거래정지|재상장|교환|이전')
    with single_collector(workspace):
        for row in keys.itertuples(index=False):
            corp=mapping.get(row.stock_code)
            status='UNMAPPED'; found=[]; hashes=[]
            if corp:
                page=1;status='SUCCESS'
                try:
                    while True:
                        data,meta=client.request('list.json',{'corp_code':corp,'bgn_de':(row.date-pd.Timedelta(days=365)).strftime('%Y%m%d'),'end_de':(row.date+pd.Timedelta(days=90)).strftime('%Y%m%d'),'last_reprt_at':'N','page_count':100,'page_no':page})
                        found+=data.get('list',[]);hashes.append(meta['source_hash'])
                        if page>=int(data.get('total_page',1)):break
                        page+=1
                except acquire.APIError as e:
                    status=str(e)
            hits=[r for r in found if terms.search(str(r.get('report_nm','')))]
            coverage.append({'stock_code':row.stock_code,'date':row.date,'status':status,'official_filings':len(found),'title_candidates':len(hits),'raw_hashes':'|'.join(hashes),'economic_payoff':'UNVERIFIED'})
            records += [{'stock_code':row.stock_code,'gap_date':str(row.date.date()),**r} for r in hits]
    pd.DataFrame(coverage).to_csv(workspace/'data/private/held_gap_official_disclosure_coverage.csv',index=False)
    pd.DataFrame(records).to_csv(workspace/'data/private/held_gap_official_disclosure_candidates.csv',index=False)
    result={'role':'OFFICIAL_DISCLOSURE_TITLE_LEADS_NOT_PAYOFF_VERIFICATION','unique_held_security_months':len(keys),'successfully_queried':sum(r['status']=='SUCCESS' for r in coverage),'unique_candidate_receipts':len({r['rcept_no'] for r in records}),'title_candidate_records_with_repeats':len(records),'new_requests':client.count,'request_budget':budget,'window_days_before_after':[365,90],'economic_returns_repaired':0,'corporate_action_payoffs':'UNVERIFIED','receipt_documents_and_exchange_adjustment_terms':'NOT_VERIFIED','old_strategy_rules_changed':False}
    write_json(output/'official_event_audit.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--workspace',required=True);p.add_argument('--ff3-root',required=True);p.add_argument('--key-file',required=True);p.add_argument('--output',required=True);p.add_argument('--budget',type=int,default=100)
    a=p.parse_args();print(json.dumps(inspect_events(a.workspace,a.ff3_root,a.key_file,a.output,a.budget)))
