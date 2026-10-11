import { spawn } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import { resolve, basename } from 'node:path';
import { root, json, csv, writeJson, writeCsv, streamHash, numeric } from './research_io.js';

interface Event { event_id: string; stock_code: string; month: string; original_unfiltered: number | null; filtered: boolean; }
interface DailyData { row_count: number; date_start: string; date_end: string; item_codes: string[]; values: Record<string, Record<string, Record<string, number | null>>>; }
const out = resolve(root, 'outputs/supplement'); const privateDir = resolve(root, '_workspace/supplement'); mkdirSync(privateDir, { recursive: true });
const dataDir = resolve(process.env.VFS_FNGUIDE_ROOT ?? resolve(root, '../fnguidedata'));
const diagnosis = csv(resolve(process.env.VFS_GAP_DIAGNOSIS ?? resolve(root, '../05_원천재구축_보관본/recollected/data/private/held_gap_source_diagnosis.csv')));
const events: Event[] = [];
for (const r of diagnosis) if (!events.some(e => e.stock_code === r.stock_code && e.month === r.date!.slice(0, 7))) events.push({ event_id: 'E' + String(events.length + 1).padStart(2, '0'), stock_code: r.stock_code!, month: r.date!.slice(0, 7), original_unfiltered: numeric(r.unfiltered), filtered: r.gt100_filtered === 'True' });
writeJson(resolve(privateDir, 'events.json'), events);
const workbook = resolve(dataDir, 'FnGuide_일간_주가.xlsx'); const extracted = resolve(privateDir, 'daily.json');
// Targeted ZIP/XML extraction avoids materializing the 1.75 GB worksheet.
const adapter = String.raw`import sys,json,zipfile,xml.etree.ElementTree as ET,re,io,datetime
events=json.load(open(sys.argv[2],encoding='utf-8')); targets={'A'+e['stock_code'] for e in events}
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
z=zipfile.ZipFile(sys.argv[1]); ss=[''.join(x.itertext()) for x in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',ns)]
months=set()
for e in events:
 y,m=map(int,e['month'].split('-')); prev=datetime.date(y,m,1)-datetime.timedelta(days=1); months.update([e['month'],prev.strftime('%Y-%m')])
def val(c):
 v=c.find('v'); t=c.get('t'); return ss[int(v.text)] if v is not None and t=='s' else float(v.text) if v is not None else None
def small(row,col):
 m=re.search(r'<c r="'+col+r'\d+"[^>]*(?:/>|>.*?</c>)',row)
 return val(ET.fromstring(m.group())) if m else None
dates={}; values={}; rows=0; items=set(); start=None; end=None
with io.TextIOWrapper(z.open('xl/worksheets/sheet1.xml'),encoding='utf-8') as f:
 pending=''
 while True:
  chunk=f.read(4*1024*1024)
  if not chunk: break
  pieces=(pending+chunk).split('</row>'); pending=pieces.pop()
  for piece in pieces:
   at=piece.rfind('<row ')
   if at<0: continue
   row=re.sub(r'\s\w+:\w+="[^"]*"','',piece[at:]+'</row>'); rows+=1
   rowno=int(re.search(r'<row r="(\d+)"',row).group(1))
   if rowno==34:
    for c in ET.fromstring(row):
     v=val(c); col=re.match('[A-Z]+',c.get('r')).group()
     if col not in ['R','S','T','U','V','W'] and isinstance(v,(int,float)):
      dt=(datetime.datetime(1899,12,30)+datetime.timedelta(days=v)).strftime('%Y-%m-%d'); start=dt if start is None else min(start,dt); end=dt if end is None else max(end,dt)
      if dt[:7] in months: dates[col]=dt
   elif rowno>34:
    code=small(row,'R'); item=small(row,'U'); items.add(item)
    if code in targets and item in ['S410000700','S410001600']:
     data={}
     for c in ET.fromstring(row):
      col=re.match('[A-Z]+',c.get('r')).group()
      if col in dates: data[dates[col]]=val(c)
     values.setdefault(code, {})[item]=data
   if rows%2000==0: print('DAILY_ROWS_SCANNED',rows,flush=True)
result={'row_count':rows,'date_start':start,'date_end':end,'item_codes':sorted(x for x in items if x),'values':values,'boundary_dates':{m:max(d for d in dates.values() if d[:7]==m) for m in months}}
open(sys.argv[3],'w',encoding='utf-8').write(json.dumps(result,allow_nan=False))
print('TARGETED_DAILY_EXTRACTION_COMPLETE',len(values),flush=True)`;
await new Promise<void>((resolvePromise, reject) => {
  const child = spawn(process.env.VFS_PYTHON ?? 'python', ['-c', adapter, workbook, resolve(privateDir, 'events.json'), extracted], { cwd: root, stdio: 'inherit' });
  child.on('error', reject); child.on('close', code => code === 0 ? resolvePromise() : reject(new Error('Daily extractor exit ' + code)));
});
const daily = json<DailyData & { boundary_dates: Record<string, string> }>(extracted);
const monthly = new Map<string, { adjusted: number | null; total: number | null }>();
// Analysis has already inspected monthly schema; here only retain target rows.
const { streamCsv } = await import('./research_io.js');
for await (const r of streamCsv(resolve(dataDir, 'FnGuide_월간연간_종목데이터.csv'))) if (r.frequency === 'monthly' && events.some(e => 'A' + e.stock_code === r.code)) monthly.set(r.code!.slice(1) + '|' + r.period, { adjusted: numeric(r.S410000700__수정주가_원__일간), total: numeric(r.KR_return_cash_dividend_included_pct) });
const audit = events.map(e => {
  const d = new Date(e.month + '-01T00:00:00Z'); d.setUTCMonth(d.getUTCMonth() - 1); const previousMonth = d.toISOString().slice(0, 7);
  const v = daily.values['A' + e.stock_code]; const price = v?.S410000700; const factor = v?.S410001600;
  const prev = price?.[daily.boundary_dates[previousMonth]!] ?? null; const current = price?.[daily.boundary_dates[e.month]!] ?? null;
  const prevFactor = factor?.[daily.boundary_dates[previousMonth]!] ?? null; const currentFactor = factor?.[daily.boundary_dates[e.month]!] ?? null;
  const implied = prev !== null && prev > 0 && current !== null ? current / prev - 1 : null;
  const m = monthly.get(e.stock_code + '|' + e.month);
  const sameLevel = m?.adjusted !== null && m?.adjusted !== undefined && current !== null ? Math.abs(m.adjusted - current) < 1e-8 : null;
  return { event_id: e.event_id, month: e.month, originally_filtered_gt100: e.filtered, daily_security_matched: !!v,
    previous_boundary_observed: prev !== null, current_boundary_observed: current !== null,
    factor_boundary_observed: prevFactor !== null && currentFactor !== null, factor_changed: prevFactor !== null && currentFactor !== null ? Math.abs(prevFactor - currentFactor) > 1e-10 : null,
    daily_monthly_adjusted_level_agrees: sameLevel, implied_adjusted_return_above100: implied !== null ? implied > 1 : null,
    original_extreme_return_agrees_with_daily: implied !== null && e.original_unfiltered !== null ? Math.abs(implied - e.original_unfiltered) < 1e-8 : null,
    dividend_return_available: m?.total !== null && m?.total !== undefined, repaired: false,
    judgment: e.filtered ? (implied !== null && implied > 1 ? 'EXTREME_ADJUSTED_MOVE_PERSISTS_NO_FILTER_RELEASE' : 'PRICE_BASIS_DIFFERENCE_OR_UNAVAILABLE_NO_PAYOFF_REPAIR') : 'GAP_NOT_ECONOMICALLY_RECONSTRUCTED' };
});
writeCsv(resolve(out, 'daily_event_audit.csv'), audit);
writeJson(resolve(out, 'daily_audit_summary.json'), { file: basename(workbook), sha256: await streamHash(workbook), worksheet: 'Sheet1', header_row: 34, security_column: 'R', item_column: 'U', date_columns: 'X:EZC', date_start: daily.date_start, date_end: daily.date_end,
  source_item_codes: daily.item_codes, inspected_items: ['S410000700: adjusted price KRW', 'S410001600: adjustment factor'], row_count: daily.row_count, unique_original_events: events.length,
  daily_securities_matched: audit.filter(r => r.daily_security_matched).length, complete_month_boundaries: audit.filter(r => r.previous_boundary_observed && r.current_boundary_observed).length,
  extreme_events: audit.filter(r => r.originally_filtered_gt100).length, extremes_persist_above100: audit.filter(r => r.originally_filtered_gt100 && r.implied_adjusted_return_above100).length,
  price_basis_disagreements: audit.filter(r => r.daily_monthly_adjusted_level_agrees === false).length,
  adjustment_factor_changes: audit.filter(r => r.factor_changed).length, returns_repaired: 0, economic_payoff_verified: false,
  limits: 'Daily snapshot and adjustment factors do not verify actual cash/share delivery, original close or tradability. Missing endpoint is not replaced by last available security price.' });
console.log(JSON.stringify({ audit }, null, 2));
