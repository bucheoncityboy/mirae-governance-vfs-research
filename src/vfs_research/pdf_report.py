"""Ten-page diagnostic report: only public aggregate data, no invented inference."""
from pathlib import Path
import os,json
import pandas as pd
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
from .data_ingest import ROOT
from .reporting import public_inputs,pct,result_summary,SOURCE,REPO


def build_pdf():
    fonts=[os.getenv('VFS_KOREAN_FONT',''),'/System/Library/Fonts/Supplemental/AppleGothic.ttf','/usr/share/fonts/truetype/nanum/NanumGothic.ttf']
    font=next((p for p in fonts if p and Path(p).exists()),None)
    if not font:raise ValueError('Set VFS_KOREAN_FONT to an authorized Korean TTF; no PDF silently emitted')
    pdfmetrics.registerFont(TTFont('ResearchKorean',font))
    styles=getSampleStyleSheet()
    for name in ['Normal','Title','Heading1','Heading2']:
        styles[name].fontName='ResearchKorean';styles[name].wordWrap='CJK'
    styles['Normal'].fontSize=10;styles['Normal'].leading=16;styles['Normal'].spaceAfter=10
    styles['Title'].fontSize=23;styles['Title'].leading=32
    styles['Heading1'].fontSize=18;styles['Heading1'].leading=26;styles['Heading1'].spaceAfter=18
    styles.add(ParagraphStyle('Small',fontName='ResearchKorean',fontSize=8.4,leading=13,wordWrap='CJK',spaceAfter=8))
    story=[];d,q,perf,status=public_inputs();s=result_summary();r=perf.set_index('strategy')
    def para(t,style='Normal'):story.append(Paragraph(t,styles[style]))
    def heading(n,t):
        if story:story.append(PageBreak())
        para(f'{n:02d} / {t}','Heading1')
    def figure(name,height=195):
        story.append(Image(str(ROOT/'outputs/figures'/f'{name}.png'),width=460,height=height));story.append(Spacer(1,8))
    def table(rows,widths=None):
        items=[[Paragraph(str(c),styles['Small']) for c in row] for row in rows]
        t=Table(items,colWidths=widths or [460/len(rows[0])]*len(rows[0]),repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8eff8')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#ccd5e0')),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story.append(t);story.append(Spacer(1,14))
    heading(1,'Investment Question / Executive Summary')
    para('Value Focus Style:<br/>공시 기반 거버넌스를 활용한<br/>가치전략의 재구현과 실증 검증','Title')
    para('독립 개인 Quant/ESG 연구 | 2026-10-10 | EMPIRICAL_LIMITED','Small')
    para('VFS의 Value 대비 성과 차이는 거버넌스 정보의 증분인가, 기존 스타일 노출인가?')
    para('미래에셋 「멀티플 탈출」(2026-05-28)의 PBR×G 규칙을 공시 시점에 맞춰 구현했다. MSCI 점수를 사외이사 비율로 바꾼 독립 재구현이며 원문 동일 재현이나 미래에셋 공동 연구가 아니다.')
    para(f"실제 공통 연속기간은 2021-07~2021-12, 월 N={len(q)}이다. VFS 누적 {pct(r.loc['VFS','total_return'])}, Value {pct(r.loc['Value','total_return'])}, 시장 {pct(r.loc['Market','total_return'])}. VFS−Value 월평균 {pct(s['mean_monthly_spread'])}p. 모든 수익률은 PRICE_RETURN_ONLY, gross 0bp다.")
    para('FF3 α/t/p/95% CI는 NOT_ESTIMATED: 6개월은 사전 최소 24개월을 충족하지 않는다. 배당·상폐·역사적 모집단·독립 OOS는 미검증이다. 손실 차이는 관찰됐지만 알파 또는 인과효과를 입증하지 못했다.')
    para('출처: 공식 원문 p20-23, p28 / OUR_RESULT: outputs/monthly_returns.csv 및 performance_summary.csv. 본 보고서는 새 VFS 결과와 과거 G 파일럿을 구분한다.','Small')
    heading(2,'Original Research / 원문을 읽는 순서')
    table([['원문 인쇄 페이지','연구 역할','우리 검증'],['p3 / p5 / p8','핵심 질문·반도체·거버넌스 배경','배경은 CONTEXT_ONLY'],['p10-15','ROE/COE·적정 멀티플','PBR만 구현; COE NOT_TESTED'],['p17-18','가치·성장 스타일의 한계','동일 모집단 Value 비교'],['p20-21 표6/7','2×2 VFS·25% cap·성과','규칙 구현, G/수익률 대체'],['p22-23 표8-10','편입종목과 스타일 특성','규모/ROE 집계, 섹터 미검증'],['p25','멀티플 탈출의 조건','독립 제한적 결론'],['p26-27 그림39','COE·MSCI 요인 계산','NOT_REPLICATED'],['p28 그림40-42','다기간 수익률·Sharpe','완전한 VFS 연간 성과 없음']],[105,165,190])
    para('p2의 모든 목차 항목은 docs/REPORT_TO_IMPLEMENTATION_MAP.md와 연결된다. 그림39는 실제 p27에 있다. 원문 표7에는 FF3 알파 검정이 없다. 원문 연평균수익률의 산식이 명확하지 않아 CAGR로 재명명하지 않았다.')
    para('FF3, paired spread HAC, PIT, 생존편향, 다중검정과 독립 OOS는 OUR EXTENSION이다. 원문의 정책·COE 결론을 이 연구가 재현했다고 주장하지 않는다.')
    heading(3,'Dataset / 실제 자료의 경계')
    gate=json.loads((ROOT/'outputs/gate_a.json').read_text())
    table([['검증한 입력','실측'],['G 공식 원시값/공시일 재검증',f"{gate['governance_verified']:,}건"],['재무자료 원시값/공시일 재검증',f"{gate['financial_verified']:,}건"],['원시 응답 객체 해시',f"{gate['raw_objects_rehashed']:,}개"],['PIT 결합 전체 표본',f"{gate['joint_companies']}기업 / {gate['joint_observations']:,} 주식-월"],['전략 공통 유효월 / 최장 연속',f"{gate['common_valid_months']} / {gate['longest_common_contiguous_months']}개월"]],[300,160])
    figure('coverage',195)
    para('2016-2020년 원문 기간에는 검증된 G·BE 결합이 없다. G/BE 매칭과 종목 모집단은 비무작위다. 캐시는 2026-10-09 수집본으로 인증키 없이 재해시했으며, 신규 공시 갱신은 수행하지 못했다. 정정 이전 원문 값은 확인되지 않았다.','Small')
    heading(4,'Methodology / 투자 규칙과 가정')
    para('6월 말까지 알려진 연간 G·전년 BE와 같은 시점 시총으로 7월 포트폴리오를 만든다. PBR = ME/(BE×100,000); ME는 천원, BE는 억원이다. 이는 우리 PIT 형성일 가정이다.')
    table([['항목','고정한 규칙'],['분류','PBR 중앙값, 동점 Low; PBR군 내부 G 중앙값, 동점 Bad'],['VFS','Low-Good과 High-Good 각각 50%; 셀 cap 25%, 최종 12.5%'],['Value','동일 적격 모집단의 Low-PBR 시총가중, 상한 추가 없음'],['보유','연간 buy-and-hold; 월별 가격 변화에 따른 비중 드리프트'],['결측','보유종목 수익률 결측 시 해당 연간 경로 중단; 사후 재가중 금지'],['비용','one-way 0/10/30bp; 매수+매도 비중 합; 초기 진입 1'],['불명확 규칙','원문 컷오프·윈저 분위수·cap 시점·거래 세부시점은 구현 가정']],[90,370])
    para('cap은 형성 시점에 검증한다. 연중 12.5%를 계속 유지하려면 추가 매매가 필요하므로 연간 보유와 혼합하지 않았다. 깨진 보유경로 후 재형성 때는 이전 비중을 알 수 없어 거래비용도 NA다.')
    para('등록된 주 분석은 동일 설계로 유지했다. 가장 긴 공통 연속기간은 수익률을 보기 전에 가용성으로 정했지만, 결측의 비무작위성은 남는다.')
    heading(5,'Performance / 공통 6개월 진단')
    rows=[['전략','6개월 누적','CAGR*','Sharpe*','MDD']]
    for x in perf.itertuples():rows.append([x.strategy,pct(x.total_return),pct(x.cagr),f'{x.sharpe:.2f}',pct(x.mdd)])
    table(rows,[75,100,100,80,105]);figure('cumulative',220)
    para('2021-07~2021-12, N=6개월, gross 0bp, 배당 미포함 가격수익률. 투자 직전 NAV=100을 포함한다. *연환산 CAGR·Sharpe는 6개월의 수학적 진단치이며 장기 기대수익률이 아니다. 누적성과와 통계적 우월성은 별개다.','Small')
    para('VFS는 Value보다 손실이 작았지만 KOSPI보다 손실이 컸다. 이 기간은 원문 2016-2026년과 다르고, 같은 MSCI 모집단도 아니다.')
    heading(6,'Risk / FF3 α는 미추정')
    para('주 검정: D = VFS−Value의 쌍별 월평균과 FF3 조정 절편. 롱은 RF를 한 번 차감하며 D는 RF를 차감하지 않는다. HAC3/6, finite-sample correction, Student-t 95% CI를 고정했다.')
    table([['검정','결과','원인'],['VFS FF3 α/t/p/CI','NA / NOT_ESTIMATED','6 < 24개월'],['Value FF3 α/t/p/CI','NA / NOT_ESTIMATED','6 < 24개월'],['VFS−Value α/t/p/CI','NA / NOT_ESTIMATED','6 < 24개월'],['D 월평균 HAC','NA / NOT_ESTIMATED','표본 부족'],['블록 부트스트랩 6/12','NA','최소 2개 블록 부족'],['12개월 rolling volatility','NA','6개월뿐']],[175,140,145])
    figure('drawdown',200)
    para('Figure 2 알파 신뢰구간은 그리지 않았다. 데이터 없는 추론 그림을 모의 숫자로 대체하지 않는다. 원문의 거버넌스 보상 해석과 FF3 통계 알파는 구분한다.','Small')
    heading(7,'Bias / 해결한 절차와 미해결 자료')
    audit=pd.read_csv(ROOT/'outputs/bias_audit.csv')
    table([['감사 상태','항목수']]+[[k,int(v)] for k,v in audit.status.value_counts().items()],[300,160])
    para('PASS는 공시 시점·결측 처리·형성 cap·설계 잠금 같은 확인된 절차에 한정한다. 코드나 테스트가 있다는 이유로 생존편향·총수익률·OOS를 PASS로 바꾸지 않았다.')
    para('UNVERIFIED: 역사적 거래소 전체 모집단, 상폐 대가, 배당과 기업행동, 사후 정정 이전 값, 역사적 업종/유동성, 법정 규모기준 및 독립 OOS. FAIL: FF3 최소 연속월 조건. 편향의 방향과 크기를 확정할 근거가 없다.')
    figure('size_G',210)
    para('사외이사 비율과 규모의 상관은 거버넌스 품질의 인과효과가 아니다. 연결자산 2조원 구분은 별도 법인의 법정 적용요건을 인증하지 못한다. PIT ROE도 노출 진단일 뿐 완전한 교란 통제가 아니다.','Small')
    heading(8,'Robustness / 모든 고정 사양 공개')
    figure('robustness',255)
    para('EW, 전체 모집단 상위5 제외, G 분위수 30/70, 한 달 PIT 지연, stale 365일, 규모군 내부 G 분류, 당시 공시 시장구분, legacy FF3, 거래비용 10/30bp까지 11개 사양을 모두 남겼다. 좋은 결과만 대표로 선택하지 않았다.')
    para('그림은 공통 주 분석 6개월이 모두 유효한 사양의 월평균 spread 기술통계다. 오차막대나 유의성 추정은 없다. 가용성이 다른 사양과 미추정 상태는 robustness.csv에서 확인한다.')
    para('등록된 민감도에는 추정 가능한 알파 검정이 없어 Holm 보정 p도 NA다. 충분한 기간이 없는 WFA/독립 OOS를 수행한 것처럼 서술하지 않는다.')
    para('PIT ROE와 12-1 가격 모멘텀은 관측 비중을 함께 적은 노출 진단으로 남겼다. EW 사양의 동일 6개월 월평균 spread는 음수로 바뀌어 가중 방식 의존성도 확인됐다. 완전한 교란 통제나 인과 추정은 아니다.')
    heading(9,'Original vs Our Findings / 결론')
    refs=pd.read_csv(ROOT/'references/original_report_reference_table.csv').head(3)
    table([['항목','REFERENCE_ONLY 원문','OUR_RESULT'],['G 정의','MSCI 다차원 점수','사외이사 비율 프록시'],['기간','2016.01~2026.04','2021.07~12, 6개월'],['수익률','현금배당 포함','PRICE_RETURN_ONLY'],['VFS','연평균 20.14% / Sharpe .75',f"누적 {pct(r.loc['VFS','total_return'])}"],['Value','연평균 12.63% / Sharpe .50',f"누적 {pct(r.loc['Value','total_return'])}"],['FF3 α','표7 미제시','NOT_ESTIMATED']],[90,185,185])
    para('표의 연평균과 6개월 누적은 서로 다른 지표다. 입력·기간·모집단·배당·윈저화를 맞추지 못해 직접 우위 비교를 할 수 없다. 원문 성과를 이번 연구 성과로 옮기지 않았다.')
    para('확인한 것은 투자규칙의 독립 구현과 짧은 가격수익률 진단이다. 투자 가능한 장기 성과와 거버넌스 증분 알파는 아직 미완료다. 고정 설계를 유지한 채 역사적 총수익률/상폐 자료, 원공시 및 새 독립기간을 확보해야 한다.')
    heading(10,'Prior Research / Reproducibility / Sources')
    para('기존 거버넌스 파일럿은 별도로 보존했다. 고정150단계 표본 2024.04~2026.03 24개월 α +0.5145%/월, HAC p=0.3888은 LEGACY_ONLY이며 비유의다. 새 VFS α로 승격하지 않았다. 기존 전수 4셀의 주 알파도 연속 3개월로 미추정이었다.')
    para('원본 FF3 120개 파일은 기준 커밋 81f3bd9와 SHA256가 모두 같다. FnGuide 종목별 parquet, DART 원시응답, 키와 미검토 이력 bundle은 새 공개 저장소에 복제하지 않았다. 저작권/재배포 권한이 불확실한 원문 PDF도 재게시하지 않는다.')
    para('공개 검증: python -m pytest -q / python -m compileall -q src / python -m vfs_research.cli verify-public. 공개 CSV로 수익률·spread·MDD·지표·문서 숫자 일치를 재계산한다. 원천 재실행은 사용자가 보유한 적법한 로컬 입력이 필요하다.')
    para(f'<link href="{SOURCE}">미래에셋 공식 원문: 「멀티플 탈출」, 유건호, 2026-05-28</link>','Small')
    para(f'<link href="{REPO}">신규 연구 저장소: mirae-governance-vfs-research</link>','Small')
    para('데이터 출처: OpenDART 공식 공시 요약과 목록, 기존 로컬 FnGuide FF3 입력. 이전 수집 캐시의 원시값·공시일·해시를 재검증했다. KRX 접근 403, Yahoo 429, Naver 가격 조회 성공은 모두 자료 접근 진단이며 총수익률·상폐 검증을 해결하지 못했다.')
    para('본 연구는 결과가 미완료임을 공개하는 독립 리서치다. 투자 권유, 미래에셋 승인, 거버넌스 인과효과 또는 유의한 알파 입증을 주장하지 않는다.')
    path=ROOT/'reports/RESEARCH_REPORT.pdf'
    doc=SimpleDocTemplate(str(path),pagesize=(595.28,841.89),leftMargin=66,rightMargin=66,topMargin=52,bottomMargin=48,title='Value Focus Style: 공시 기반 거버넌스 가치전략 실증 검증',author='Independent personal research')
    def footer(canvas,doc):
        canvas.setFont('ResearchKorean',8);canvas.setFillColor(colors.HexColor('#536174'));canvas.drawString(66,25,'VFS independent research | EMPIRICAL_LIMITED | PRICE_RETURN_ONLY');canvas.drawRightString(529,25,str(doc.page))
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print('PDF_CREATED',path)
