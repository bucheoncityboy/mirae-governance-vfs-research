import { createReadStream, readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { parse } from 'csv-parse';
import { parse as parseSync } from 'csv-parse/sync';
import { resolve } from 'node:path';

export const root = resolve(import.meta.dirname, '..');
export type CsvRow = Record<string, string>;
export function json<T>(path: string): T { return JSON.parse(readFileSync(path, 'utf8')) as T; }
export function writeJson(path: string, value: unknown): void { writeFileSync(path, JSON.stringify(value, null, 2) + '\n'); }
export function csv(path: string): CsvRow[] { return parseSync(readFileSync(path), { columns: true, bom: true }) as CsvRow[]; }
export async function* streamCsv(path: string): AsyncGenerator<CsvRow> {
  const parser = createReadStream(path).pipe(parse({ columns: true, bom: true }));
  for await (const row of parser) yield row as CsvRow;
}
export function numeric(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined || value === '' || (typeof value === 'string' && value.trim() === '')) return null;
  const n = Number(value); return Number.isFinite(n) ? n : null;
}
export const mean = (x: number[]): number => x.reduce((a, b) => a + b, 0) / x.length;
export function median(x: number[]): number {
  const a = [...x].sort((a, b) => a - b); const n = a.length;
  return n ? ((a[Math.floor(n / 2)]! + a[Math.floor((n - 1) / 2)]!) / 2) : NaN;
}
export function variance(x: number[]): number { const m = mean(x); return x.reduce((a, b) => a + (b - m) ** 2, 0) / (x.length - 1); }
export function hash(path: string): string { return createHash('sha256').update(readFileSync(path)).digest('hex'); }
export async function streamHash(path: string): Promise<string> { const h = createHash('sha256'); for await (const b of createReadStream(path)) h.update(b as Buffer); return h.digest('hex'); }
export function writeCsv(path: string, rows: Record<string, string | number | boolean | null>[]): void {
  if (!rows.length) throw new Error('Cannot publish empty table: ' + path);
  const keys = Object.keys(rows[0]!);
  const field = (v: unknown): string => '"' + String(v ?? '').replaceAll('"', '""') + '"';
  writeFileSync(path, keys.map(field).join(',') + '\n' + rows.map(r => keys.map(k => field(r[k])).join(',')).join('\n') + '\n');
}
export function months(start: string, end: string): string[] {
  const result: string[] = []; const d = new Date(start + '-01T00:00:00Z');
  while (d.toISOString().slice(0, 7) <= end) { result.push(d.toISOString().slice(0, 7)); d.setUTCMonth(d.getUTCMonth() + 1); }
  return result;
}
export function outputDir(): string { const p = resolve(root, 'outputs/supplement'); mkdirSync(p, { recursive: true }); return p; }
