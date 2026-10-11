"""Official evidence acquisition and guarded economic valuation.

Private security identities and bodies stay outside Git. A disclosure is evidence
of an event, not sufficient evidence of a realized monthly holding return.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd

from .data_ingest import ROOT, digest
from .reconstruction import write_json


def parse_nodes(page):
    nodes = []
    for block in re.split(r'var node\d+ = \{\};', page)[1:]:
        node = dict(re.findall(r"node\d+\['(\w+)'\]\s*=\s*\"([^\"]*)\"", block))
        if all(k in node for k in ['rcpNo', 'dcmNo', 'eleId', 'offset', 'length', 'dtd']):
            nodes.append(node)
    if not nodes:
        # Exchange HTML disclosures use an observed direct viewDoc invocation.
        for args in re.findall(r'viewDoc\(((?:"[^"]*",?\s*){6,7})\)', page):
            values = re.findall(r'"([^"]*)"', args)
            if len(values) >= 6 and values[0].isdigit() and values[1].isdigit():
                nodes.append(dict(zip(['rcpNo','dcmNo','eleId','offset','length','dtd'], values[:6]), text='Official exchange HTML body'))
    return nodes


def plain_text(body):
    try:
        text = body.decode('utf-8')
    except UnicodeDecodeError:
        text = body.decode('cp949')
    text = re.sub(r'<(?:script|style)\b[^>]*>.*?</(?:script|style)>', '', text, flags=re.S|re.I)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', text))).strip()


def fetch_body(url, cache, budget):
    """No credential-bearing URLs; cache digest checked on every reuse."""
    if not url.startswith('https://dart.fss.or.kr/') or 'crtfc_key' in url:
        raise ValueError('only public official DART URLs allowed')
    name = hashlib.sha256(url.encode()).hexdigest()
    target = cache / (name + '.bin')
    meta_file = cache / (name + '.json')
    if target.exists() and meta_file.exists():
        meta = json.loads(meta_file.read_text())
        if digest(target) != meta['sha256']:
            raise ValueError('official evidence cache hash mismatch')
        return target.read_bytes(), meta
    if budget['requests'] >= budget['cap']:
        raise ValueError('official evidence request cap reached')
    budget['requests'] += 1
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'VFSResearch/1.0', 'Accept': 'text/html'})
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read()
            status = response.status
        meta = {'url': url, 'http_status': status, 'bytes': len(body),
                'sha256': hashlib.sha256(body).hexdigest(),
                'retrieved_at_utc': datetime.now(timezone.utc).isoformat()}
    except Exception as error:
        # Exception messages can include request URLs: record only the type.
        body = b''
        meta = {'url': url, 'http_status': None, 'bytes': 0,
                'sha256': hashlib.sha256(body).hexdigest(),
                'error_type': type(error).__name__,
                'retrieved_at_utc': datetime.now(timezone.utc).isoformat()}
    target.write_bytes(body); target.chmod(0o600)
    write_json(meta_file, meta); meta_file.chmod(0o600)
    return body, meta


def collect_selected(workspace, private_dir, selections):
    """Read a private receipt selection and collect relevant official sections."""
    workspace, private_dir = Path(workspace).resolve(), Path(private_dir).resolve()
    if private_dir == ROOT or ROOT in private_dir.parents:
        raise ValueError('private evidence must remain outside repository')
    lock = json.loads((ROOT/'config/economic_recovery_followup_lock.json').read_text())
    if digest(ROOT/'config/economic_recovery_followup.yaml') != lock['sha256']:
        raise ValueError('economic follow-up lock mismatch')
    private_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    cache = private_dir/'official-bodies'; cache.mkdir(mode=0o700, exist_ok=True)
    existing_requests = len(list(cache.glob('*.json')))
    budget = {'cap': max(0,100-existing_requests), 'requests': 0}
    records = []
    for selection in json.loads(Path(selections).read_text()):
        receipt = selection['receipt']
        if not re.fullmatch(r'\d{14}', receipt):
            raise ValueError('invalid receipt')
        main_url = 'https://dart.fss.or.kr/dsaf001/main.do?rcpNo='+receipt
        body, meta = fetch_body(main_url, cache, budget)
        nodes = parse_nodes(body.decode('utf8', errors='replace'))
        selected = [n for n in nodes if re.search(selection['sections'], n.get('text', ''))]
        if not selected and nodes:
            selected = nodes[:1]
        for i, node in enumerate(selected):
            url = 'https://dart.fss.or.kr/report/viewer.do?'+urllib.parse.urlencode({k:node[k] for k in ['rcpNo','dcmNo','eleId','offset','length','dtd']})
            raw, section_meta = fetch_body(url, cache, budget)
            text = plain_text(raw)
            (private_dir/f"{selection['event_id']}-{receipt}-{i}.txt").write_text(text)
            records.append({'event_id':selection['event_id'], 'receipt':receipt,
                            'section':node.get('text',''), 'body_sha256':section_meta['sha256'],
                            'body_bytes':len(raw), 'body_text_characters':len(text),
                            'url':url, 'retrieved_at_utc':section_meta['retrieved_at_utc'],
                            'status':'BODY_AVAILABLE' if len(text)>5 else 'ACCESS_BLOCKED_OR_EMPTY'})
        if not nodes:
            records.append({'event_id':selection['event_id'], 'receipt':receipt,
                            'section':'NO_VIEWER_NODES', 'body_sha256':meta['sha256'],
                            'body_bytes':len(body), 'body_text_characters':0,
                            'url':main_url, 'retrieved_at_utc':meta['retrieved_at_utc'],
                            'status':'ACCESS_BLOCKED_OR_EMPTY'})
    pd.DataFrame(records).to_csv(private_dir/'section_inventory.csv', index=False)
    write_json(private_dir/'collection_receipt.json', {'new_public_web_requests':budget['requests'],
               'total_cached_public_web_requests':existing_requests+budget['requests'],
               'request_cap':100, 'sections':len(records),
               'successful_sections':sum(r['status']=='BODY_AVAILABLE' for r in records),
               'source_redistribution':'NOT_AUTHORIZED_PRIVATE_ONLY', 'API_key_used':False})
    return {'new_requests':budget['requests'], 'sections':len(records),
            'successful_sections':sum(r['status']=='BODY_AVAILABLE' for r in records)}


def economic_return(previous_price, month_end_price, quantity_ratio=1., cash=0.,
                    rights=0., status='UNVERIFIED', basis_verified=False,
                    source_already_adjusted=False):
    """A per-old-share valuation; does not assign or infer any event terms."""
    if status != 'VERIFIED_CORRECTABLE' or not basis_verified:
        raise ValueError('unverified economic payoff cannot extend NAV')
    values = [previous_price, month_end_price, quantity_ratio, cash, rights]
    if not np.isfinite(values).all() or previous_price <= 0 or min(values[1:]) < 0:
        raise ValueError('invalid per-share valuation')
    if source_already_adjusted and (quantity_ratio != 1 or cash != 0 or rights != 0):
        raise ValueError('double adjustment is forbidden')
    return (quantity_ratio * month_end_price + cash + rights) / previous_price - 1


def missing_contribution_scenarios(aggregate):
    """Isolated assumptions, never a reconstructed portfolio monthly return."""
    rows=[]
    for row in aggregate.itertuples():
        if not 0 <= row.missing_weight <= 1:
            raise ValueError('invalid missing exposure')
        for assumption in [-1., -.5, .5, 1.]:
            rows.append({'date':row.date,'strategy':row.strategy,
                         'unknown_position_weight':row.missing_weight,
                         'assumed_asset_return':assumption,
                         'unknown_position_contribution_pp':100*row.missing_weight*assumption,
                         'role':'ASSUMPTION_ONLY_NOT_OBSERVED_RETURN',
                         'observed_portfolio_return':np.nan,
                         'extends_observed_NAV':False})
    return pd.DataFrame(rows)


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--workspace',required=True); p.add_argument('--private-dir',required=True)
    p.add_argument('--selections',required=True)
    a=p.parse_args()
    print(json.dumps(collect_selected(a.workspace,a.private_dir,a.selections)))
