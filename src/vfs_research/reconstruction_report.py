"""Separate current-vintage evidence appendix; the original narrative is preserved."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .data_ingest import ROOT


def build_appendix():
    out = ROOT / 'outputs/reconstruction'
    summary = json.loads((out / 'raw_replay_summary.json').read_text())
    if summary['status'] != 'RAW_SOURCE_VFS_REPLAY_COMPLETED':
        raise ValueError('appendix requires completed raw replay')
    audit = json.loads((out / 'return_audit_summary.json').read_text())
    acquisition = json.loads((out / 'collection_summary.json').read_text())
    new = pd.read_csv(out / 'recollected_monthly_returns.csv', parse_dates=['date'])
    old = pd.read_csv(ROOT / 'snapshots/public-c8abb0f/monthly_returns.csv', parse_dates=['date'])
    own = pd.read_csv(out / 'recollected_vfs_strategy_summary.csv')
    paired = pd.read_csv(out / 'recollected_performance_summary.csv')
    neutral = pd.read_csv(out / 'exploratory_g_neutral_monthly.csv', parse_dates=['date'])
    gaps = pd.read_csv(out / 'recollected_held_missing_monthly.csv')
    images = out / 'figures'
    images.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size': 10, 'svg.fonttype': 'none'})
    fig, ax = plt.subplots(figsize=(8, 3.5), constrained_layout=True)
    vfs = own.loc[own.strategy.eq('VFS')].iloc[0]
    dates = new.loc[new.date.between(vfs.start, vfs.end), 'date']
    for label, frame, style in [('Published snapshot', old, '--'), ('Fresh raw replay', new, '-')]:
        r = frame.set_index('date').loc[dates, 'VFS']
        values = np.r_[100., (1 + r).cumprod().to_numpy() * 100]
        x = pd.DatetimeIndex([dates.iloc[0] - pd.offsets.MonthBegin(1), *dates])
        ax.plot(x, values, style, label=label, linewidth=2)
    ax.set(title=f"VFS raw replay vs published snapshot | N={len(dates)}",
           ylabel='Price NAV (initial 100)')
    ax.legend(); ax.grid(alpha=.2)
    fig.savefig(images / 'replay_comparison.svg'); fig.savefig(images / 'replay_comparison.png', dpi=160); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 3.5), constrained_layout=True)
    labels = ['Prior inner-match\nmissing', 'All source\nmissing', 'No price row\npreserved', 'Full-source\n>100% filter', 'Study-window\n>100% filter']
    values = [audit['previous_inner_join_missing_count'], audit['missing_returns'], audit['missing_price_rows_preserved'], audit['gt100_filtered'], audit['study_2016_01_to_2026_04_gt100_filtered']]
    bars = ax.bar(labels, values, color=['#8b95a6', '#2368a0', '#d18b34', '#6d7f98', '#5b9f96'])
    ax.bar_label(bars, padding=3); ax.set_ylim(0, max(values)*1.2)
    ax.set(title='Return audit | scopes overlap; bars are not additive', ylabel='Source records')
    fig.savefig(images / 'return_audit.svg'); fig.savefig(images / 'return_audit.png', dpi=160); plt.close(fig)
    q = neutral.loc[neutral.comparison_window]
    if len(q):
        fig, ax = plt.subplots(figsize=(8, 3.5), constrained_layout=True)
        x=pd.DatetimeIndex([q.date.iloc[0]-pd.offsets.MonthBegin(1),*q.date])
        for s in ['VFS', 'GNeutral']:
            ax.plot(x, np.r_[100.,(1+q[s]).cumprod().to_numpy()*100], label=s)
        ax.set_xticks(x);ax.set_xticklabels(x.strftime('%Y-%m'))
        ax.set(title=f'Exploratory PBR-budget-matched comparison | N={len(q)}', ylabel='Price NAV (initial 100)')
        ax.legend(); ax.grid(alpha=.2)
        fig.savefig(images / 'g_neutral.svg'); fig.savefig(images / 'g_neutral.png', dpi=160); plt.close(fig)
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
    font = next((p for p in ['/System/Library/Fonts/Supplemental/AppleGothic.ttf', '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'] if Path(p).exists()), None)
    if not font:
        raise ValueError('Korean font required')
    pdfmetrics.registerFont(TTFont('RebuildKorean', font))
    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName='RebuildKorean'; style.wordWrap='CJK'
    styles['Normal'].fontSize=10; styles['Normal'].leading=16; styles['Normal'].spaceAfter=10
    styles['Heading1'].fontSize=19; styles['Heading1'].leading=27; styles['Heading1'].spaceAfter=15
    story=[]
    def p(text, style='Normal'): story.append(Paragraph(text, styles[style]))
    def table(rows, widths):
        t=Table([[Paragraph(str(c),styles['Normal']) for c in row] for row in rows],colWidths=widths,repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8eff8')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#ccd5e0')),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
        story.extend([t,Spacer(1,12)])
    def image(name): story.append(Image(str(images / (name+'.png')),width=460,height=201))
    p('VFS 원천 재구축 검증 부록', 'Heading1')
    p('2026-10-11 KST | 기존 보고서에 대한 후속 검증 | EMPIRICAL_LIMITED')
    p('원문 p20-23의 투자규칙과 p28의 다기간 검증을 이어간다. 이전 로컬 입력 없이 GitHub 기준 코드와 FF3 입력을 새로 받고, 공식 OpenDART 공시를 다시 수집했다. 기존 본문과 6개월·8개월 결과는 별도 스냅샷으로 보존했다.')
    p(f"공식 과거 목록 {acquisition['historical_filings']:,}건, 원패널 고유 법인 매핑 {acquisition['mapped_source_tickers']:,}종목, 수집 작업 {acquisition['company_report_jobs']:,}개. 새 자료에서 G {summary['current_evidence']['governance_verified']:,}건·재무 {summary['current_evidence']['financial_verified']:,}건을 접수번호·공시일·이사 수·KRW 장부자본·원응답 해시로 검증했다.")
    rows=[['분석','관측 월수','새 원천 누적 가격수익률']]
    rows += [[r.strategy+' 공통 비교',r.n_months,f'{r.total_return*100:.4f}%'] for r in paired.itertuples()]
    rows += [[r.strategy+' 자체 연속기간',r.n_months,f'{r.total_return*100:.4f}%'] for r in own.itertuples() if r.strategy=='VFS']
    table(rows,[170,80,210]); image('replay_comparison')
    p('기존 월수익률과 비교한 차이(절대 허용오차 1e-12): '+str(summary['changed_monthly_returns_above_1e_12'])+'. 원자료 SHA의 일치 여부와 경제적 성과의 일치는 구분한다. 정정 이전 공시 값은 여전히 미검증이다.')
    story.append(PageBreak())
    p('결측과 가격 필터: 실제 보유경로 감사', 'Heading1')
    p(f"전체 stock_returns {audit['stock_return_rows']:,}행의 결측은 {audit['missing_returns']:,}건이다. 기존 내부 조인은 가격 행이 없는 {audit['missing_price_rows_preserved']:,}건을 제외해 결측 {audit['previous_inner_join_missing_count']:,}건만 확인했다. 새 감사는 왼쪽 조인으로 모든 원수익률 행을 남긴다. 전략 입력과 수익률은 변경하지 않았다.")
    image('return_audit')
    p(f"전체 1999-12~2026-05 가격 필터는 {audit['gt100_filtered']}건이다. VFS 목표 2016-01~2026-04에는 필터 {audit['study_2016_01_to_2026_04_gt100_filtered']}건·결측 {audit['study_2016_01_to_2026_04_missing_returns']}건이 있다. 이 수치는 편입종목 결측과 다르며 서로 더할 수 없다.")
    table([['전략','첫 연간 중단 월수','결측 보유 기록']]+[[s,len(x),int(x.missing_held_securities.sum())] for s,x in gaps.groupby('strategy')],[170,145,145])
    p('배당·액면분할·합병·상폐 대가의 경제적 수익률 수정은 0건이다. 결측 종목 사후 제거, 결측 0 대체, 극단수익률 자동 복원은 수행하지 않았다. 따라서 원천 재구축이 장기 투자성과 검증의 완료를 뜻하지 않는다.')
    events=json.loads((out/'official_event_audit.json').read_text())
    final=json.loads((ROOT/'outputs/final/completion_status.json').read_text())
    p(f"이전 제목 탐색은 후보 {events['unique_candidate_receipts']}개였다. 이번 감사는 11개 사건의 {final['official_documents']}개 접수번호·{final['official_sections']}개 공식 본문 절을 읽었다. 계약상 교환 조건과 일정 일부는 확인했으나 양월 평가가격·수량·실제 지급·조정 기준은 미검증이다. 2021년 12월 권리 전환과 형성 이전 거래정지도 확인해 투자 가능성의 한계를 분리했다. 수정은 0건이다.")
    story.append(PageBreak())
    p('G-neutral 탐색 비교와 남은 검증', 'Heading1')
    p(f"같은 PIT 모집단에서 Low/High PBR 예산을 50:50으로 맞추고 G 선별을 제거했다. 구간 내 lagged-ME capped-VW를 사용하며 셀 cap 25%를 유지했다. VFS와 공통 연속기간은 {len(q)}개월이다. 연속 PBR 분포·규모·산업이 완전히 같아지는 비교는 아니다.")
    if len(q): image('g_neutral')
    status=pd.read_csv(out/'followup_multiplicity.csv')
    p(f"FF3 및 G-neutral spread의 HAC3/6 검정: 추정 가능한 검정 {int(status.p_hac.notna().sum())}개 / 8개 사양. 최소 연속 24개월 미충족에는 alpha/t/p/CI를 NA로 남긴다. 추정 가능한 경우 Holm 보정을 적용하고, 개별 95% HAC 구간을 동시 신뢰구간으로 표현하지 않는다.")
    p(f"수집 로그 {acquisition['recorded_api_requests']:,}건에 응답 상태와 수집시각을 남겼다. 재시작 중 중복 기록 {acquisition['duplicate_request_ids']}건도 보존했다. 캐시 해시 검증 실패는 {acquisition['cache_hash_failures']}건이다. 실제 요청량은 API 계정의 최종 과금·쿼터 기록과 별개다.")
    p('MSCI G와 사외이사 비율의 차이, 법정 요건·규모 혼동, 역사적 거래소 전체 모집단, 총수익률·상폐 대가, 정정 이전 공시, 독립 OOS는 미검증이다. 공개된 기존 FF3 팩터를 사용하는 보조 검정도 조건부 모델이다. 기존 비유의 거버넌스 파일럿을 새 VFS 결과로 바꾸지 않았다.')
    p('COMPLETE_LIMITED_EVIDENCE: 원천 재현·사건 감사·미추정 결론을 갖춘 한정 연구의 완결이다. 장기 투자성과 검증이 아니다. KRX 역사적 가격은 로그인 요구로 미확보다. 상세 근거: docs/ECONOMIC_RETURN_RECOVERY.md와 outputs/final. 원천·개별 파생자료·키는 GitHub에 올리지 않았고 재배포 권한은 미확정이다.')
    path=ROOT/'reports/PUBLIC_SOURCE_REBUILD_APPENDIX.pdf'
    doc=SimpleDocTemplate(str(path),pagesize=(595.28,841.89),leftMargin=66,rightMargin=66,topMargin=48,bottomMargin=48,title='VFS public source rebuild evidence appendix')
    def footer(canvas,doc):
        canvas.setFont('RebuildKorean',8);canvas.drawString(66,24,'VFS source rebuild | PRICE_RETURN_ONLY | EMPIRICAL_LIMITED');canvas.drawRightString(529,24,str(doc.page))
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    for svg in images.glob('*.svg'):
        svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    return path


if __name__ == '__main__':
    print(build_appendix())
