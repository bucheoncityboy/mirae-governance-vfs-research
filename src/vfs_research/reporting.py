from pathlib import Path
import hashlib,json,re,html
import numpy as np
import pandas as pd
from .data_ingest import ROOT,digest
from .stats import performance
from .strategy_diagnostics import vfs_observed_window,vfs_strategy_summary,export_strategy_diagnostics

SOURCE='https://securities.miraeasset.com/bbs/maildownload/20260527170512707_154'
REPO='https://github.com/bucheoncityboy/mirae-governance-vfs-research'


def public_inputs():
    d=pd.read_csv(ROOT/'outputs/monthly_returns.csv',parse_dates=['date'])
    return d,d.loc[d.primary_window].copy(),pd.read_csv(ROOT/'outputs/performance_summary.csv'),json.loads((ROOT/'outputs/results_status.json').read_text())


def pct(x):return 'NA' if pd.isna(x) else f'{x*100:+.2f}%'


def result_summary():
    d,q,perf,s=public_inputs();means=float(q.spread.mean()) if len(q) else None
    own=vfs_strategy_summary(d);window=vfs_observed_window(d)
    return {'label':'OUR_RESULT','research_focus':'VFS_PORTFOLIO_BACKTEST','ff3_role':'SUPPLEMENTARY_ATTRIBUTION','vfs_own_window':{'start':str(window.date.min().date()),'end':str(window.date.max().date()),'n_months':len(window),'valid_months_total':int(d.VFS.notna().sum()),'metrics':own.replace({np.nan:None}).to_dict('records')},'start':s['primary_start'],'end':s['primary_end'],'n_months':len(q),'common_valid_months':s['common_valid_months'],'joint_companies':s['joint_companies'],'return_basis':'PRICE_RETURN_ONLY','cost_basis':'gross_0bp','mean_monthly_spread':means,'alpha_status':s['primary_alpha'],'independent_oos':s['independent_oos'],'metrics':perf.replace({np.nan:None}).to_dict('records')}


def strategy_brief():
    s=result_summary()['vfs_own_window'];r=pd.DataFrame(s['metrics']).set_index('strategy')
    return f"VFS 자체의 최장 연속 관측은 {s['start'][:7]}~{s['end'][:7]}({s['n_months']}개월)이며, 누적 가격수익률은 VFS {pct(r.loc['VFS','total_return'])}, 같은 기간 KOSPI {pct(r.loc['Market','total_return'])}입니다."


def performance_table(perf):
    lines=['| 전략 (OUR_RESULT) | 6개월 누적 | 연환산 CAGR* | 연환산 변동성* | Sharpe* | 월간 MDD |','| --- | ---: | ---: | ---: | ---: | ---: |']
    for r in perf.itertuples():lines.append(f'| {r.strategy} | {pct(r.total_return)} | {pct(r.cagr)} | {r.volatility*100:.2f}% | {r.sharpe:.2f} | {pct(r.mdd)} |')
    return '\n'.join(lines)


def figures():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    d,q,perf,s=public_inputs();out=ROOT/'outputs/figures';out.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
    colors={'VFS':'#2563eb','Value':'#c56b35','Market':'#64748b'}
    caption=f"OUR_RESULT | {s['primary_start'][:7]} to {s['primary_end'][:7]} | N={len(q)} months | PRICE_RETURN_ONLY | gross, 0bp | OOS unverified"
    def save(fig,name,cap=caption):
        fig.text(.02,.012,cap,fontsize=8,color='#475569');fig.tight_layout(rect=(0,.055,1,1));fig.savefig(out/(name+'.png'),dpi=180);fig.savefig(out/(name+'.svg'));plt.close(fig)
        svg=out/(name+'.svg');svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    own=vfs_observed_window(d);own_x=pd.DatetimeIndex([own.date.iloc[0]-pd.Timedelta(days=1)]+list(own.date+pd.offsets.MonthEnd(0)))
    fig,ax=plt.subplots(figsize=(9,4.4))
    for z in ['VFS','Market']:ax.plot(own_x,np.r_[100,100*(1+own[z]).cumprod()],label=z,color=colors[z],linewidth=2)
    ax.set(title='VFS observed holding path: independent of Value / FF3 availability',ylabel='Index (100 before first holding month)');ax.legend();ax.grid(alpha=.15)
    save(fig,'vfs_observed',f"OUR_RESULT | {own.date.min():%Y-%m} to {own.date.max():%Y-%m} | N={len(own)} | PRICE_RETURN_ONLY | gross 0bp | separate 6-month paired comparison")
    x=pd.DatetimeIndex([q.date.iloc[0]-pd.Timedelta(days=1)]+list(q.date+pd.offsets.MonthEnd(0)))
    fig,ax=plt.subplots(figsize=(9,4.4))
    for z in colors:ax.plot(x,np.r_[100,100*(1+q[z]).cumprod()],label=z,color=colors[z],linewidth=2)
    ax.set(title='Figure 1. Common contiguous diagnostic: cumulative index',ylabel='Index (100 before first holding month)');ax.legend();ax.grid(alpha=.15);save(fig,'cumulative')
    fig,ax=plt.subplots(figsize=(9,4))
    ax.bar(q.date,q.spread*100,width=20,color=['#2563eb' if r>=0 else '#c56b35' for r in q.spread]);ax.axhline(0,color='#64748b',lw=.8);ax.set(title='Paired monthly VFS - Value spread',ylabel='Percentage points / month');save(fig,'spread')
    fig,ax=plt.subplots(figsize=(9,4))
    for z in ['VFS','Value','Market']:
        nav=np.r_[1,(1+q[z]).cumprod()];ax.plot(x,(nav/np.maximum.accumulate(nav)-1)*100,label=z,color=colors[z])
    ax.set(title='Monthly drawdown: baseline NAV included',ylabel='% below prior peak');ax.legend();save(fig,'drawdown')
    c=pd.read_csv(ROOT/'outputs/coverage_matrix.csv',parse_dates=['date'])
    fig,ax=plt.subplots(figsize=(9,4))
    for name in ['population_n','g_pit_n','financial_pit_n','joint_n']:ax.plot(c.date,c[name],label=name)
    ax.set(title='Original 2016-2026 horizon versus actual public-data coverage',ylabel='Companies per month');ax.legend(fontsize=8);save(fig,'coverage','OUR_RESULT | 2016-01 to 2026-04 | company counts; not independent monthly observations | dividend/delisting unverified')
    c=pd.read_csv(ROOT/'outputs/cell_formation_coverage.csv',parse_dates=['date'])
    fig,ax=plt.subplots(figsize=(9,4))
    for cell,z in c.groupby('cell'):ax.plot(z.date,z.n,marker='o',label=cell)
    ax.set(title='Annual formation counts: four cells (returns may still be missing)',ylabel='Companies');ax.legend(fontsize=8);save(fig,'cells','OUR_RESULT | annual July formations 2016-2025 | counts; median G ties stay Bad | no MSCI score')
    r=pd.read_csv(ROOT/'outputs/robustness.csv');r=r.loc[r.same_primary_months_valid]
    fig,ax=plt.subplots(figsize=(9,5))
    ax.barh(r.spec_id,r.primary_window_mean_spread*100,color='#64748b');ax.axvline(0,color='#0f172a',lw=.8);ax.set(title='Sensitivity: same six primary months, descriptive mean only',xlabel='VFS - Value mean, percentage points / month');save(fig,'robustness','OUR_RESULT | 2021-07 to 2021-12 | N=6 | PRICE_RETURN_ONLY | gross except cost rows | no inferential CI')
    z=pd.read_csv(ROOT/'outputs/size_G_diagnostics.csv');fig,ax=plt.subplots(figsize=(9,4));ax.plot(z.year,z.G_log_ME_correlation,marker='o',color='#2563eb');ax.set(title='Governance proxy versus firm size: formation cross-section',ylabel='Correlation (G, log market cap)',xlabel='Formation year');save(fig,'size_G','OUR_RESULT | July 2021-2025 cross-sections | correlation only | separate-entity legal threshold unverified')
    print('ACTUAL_FIGURES',8,'VFS_OWN_AND_COMPARATOR_WINDOWS_SEPARATE')


def narrative():
    d,q,perf,s=public_inputs();summary=result_summary();table=performance_table(perf);r=perf.set_index('strategy')
    brief=f"Value와 동일 조건으로 비교하는 공통 연속 기간은 {s['primary_start'][:7]}~{s['primary_end'][:7]}({len(q)}개월)입니다. 이 기간 누적 가격수익률은 VFS {pct(r.loc['VFS','total_return'])}, Value {pct(r.loc['Value','total_return'])}, KOSPI {pct(r.loc['Market','total_return'])}이며, VFS−Value 월평균 차이는 {pct(summary['mean_monthly_spread'])}p입니다."
    own_brief=strategy_brief()
    pages_link='https://bucheoncityboy.github.io/mirae-governance-vfs-research/'
    return f'''# Value Focus Style | 공시 기반 거버넌스 가치전략의 독립 재구현 및 검증

**미래에셋의 VFS 투자규칙을 실제 공시 시점에 맞춰 구성하면, 어떤 수익률·위험·보유경로가 나타나는가?** 유건호 연구원의 「멀티플 탈출」(2026-05-28)을 따라 VFS 자체의 백테스트와 Value·시장 비교를 수행하는 독립 개인 연구입니다.

**VFS 백테스트 상태: 부분 관측 / EMPIRICAL_LIMITED.** {own_brief} {brief} 원천 PIT 결합 표본은 {s['joint_companies']}기업·{s['joint_observations']:,} 주식-월입니다. MSCI G 대신 사외이사 비율을 썼으며 **PRICE_RETURN_ONLY**, gross 0bp, 배당·상폐·독립 OOS 미검증입니다. FF3는 성과 해석을 위한 보조 검정으로 하단에 구분했습니다.

[공식 원문 PDF]({SOURCE}) · [독립 연구보고서](reports/RESEARCH_REPORT.pdf) · [Executive Brief](reports/EXECUTIVE_BRIEF.md) · [VFS 보유경로](outputs/figures/vfs_observed.png) · [배포 대시보드]({pages_link}) · [재현 방법](docs/REPRODUCIBILITY.md)

읽는 순서: 원문 배경 p5 → 가치평가 가설 p10 → 스타일 비교 p17 → **[VFS 규칙 p20](#04-rebuilding-the-vfs-strategy)** → **[원문과 실증 p21-23](#05-original-results-vs-our-backtest)** → **[다기간 검증 p28](#06-alpha-regimes--robustness)** → 결론 p25. [전체 목차·근거 매핑](docs/REPORT_TO_IMPLEMENTATION_MAP.md)은 p2의 모든 항목과 본문 표·그림을 연결합니다.

## 00. Research Question & Findings

**원문 (p3 Executive Summary)** — 저PBR만으로는 가치 함정을 구분하기 어려워, 거버넌스가 우수한 저PBR와 고PBR 기업을 함께 담는 전략을 제안합니다.

**우리의 구현** — 같은 모집단에서 VFS와 Value를 비교하고, 수익률 차이와 FF3 조정 차이를 분리했습니다. 결과를 보기 전 [설계 커밋](https://github.com/bucheoncityboy/mirae-governance-vfs-research/commit/09a105ce651bc28eaad1e0993b12678a41acf61f)을 남겼지만, 이전 G 연구를 알고 있었으므로 탐색 연구입니다.

**실증 결과** — {own_brief} {brief}

![VFS 자체의 실제 연속 보유경로: 2021-07~2022-02 N=8 PRICE_RETURN_ONLY gross 0bp; Value 비교는 별도 공통 6개월](outputs/figures/vfs_observed.png)

**판정: ADAPTED / 부분 관측.** VFS 자체의 8개월 기록과 세 전략의 공통 6개월 비교는 서로 다른 분석입니다. 원수익과 보유경로를 먼저 검증하며, FF3 추정 가능 여부로 VFS 백테스트의 존재 여부를 판정하지 않습니다. [보유경로 중단 원인과 구현 가정](docs/VFS_BACKTEST_DIAGNOSIS.md).

## 01. Why Governance?

**원문 (p5 「두개의 날개, 반도체와 거버넌스 개혁」, p8)** — 반도체 이익과 거버넌스 개혁을 시장 배경으로 설명합니다.

**우리의 구현** — 이 배경에서 투자 규칙의 검증 질문을 가져왔습니다. 정책 효과나 반도체 경기의 인과효과를 재추정하지 않았습니다.

**실증 결과** — 정책 이벤트 분석 **NOT_TESTED**. [규모·G 진단](outputs/size_G_diagnostics.csv)은 이사회 비율과 기업규모의 혼동 가능성을 점검할 뿐입니다.

**판정: CONTEXT_ONLY.** 사외이사 비율은 종합 거버넌스 품질이 아니며, 법정 선임요건·기업규모와 함께 움직일 수 있습니다.

## 02. From Valuation to Hypothesis

**원문 (p10 「코스피의 적정 멀티플을 찾아서」, p11·13·15)** — ROE와 COE를 연결해 적정 멀티플과 시나리오를 논의합니다.

**우리의 구현** — [공시일 PIT](src/vfs_research/pit_features.py)와 공식 재무자료로 확인한 BE를 이용해 형성 시점 PBR을 계산했습니다. COE 모형, 전망 ROE와 적정 PBR 예측은 구현하지 않았습니다.

**실증 결과** — 원시 증빙 {json.loads((ROOT/'outputs/gate_a.json').read_text())['raw_objects_rehashed']:,}개 해시를 다시 확인했습니다. 과거 G와 재무자료가 동시에 연결되는 기간은 2021년 이후이며 [월별 커버리지](outputs/coverage_matrix.csv)에 공백을 남겼습니다.

![실제 월별 데이터 커버리지: 2016-01~2026-04 기업수, 배당 및 상폐 미검증](outputs/figures/coverage.png)

**판정: ADAPTED PBR / NOT_TESTED COE.** 주가 상승이나 이사회 비율만으로 할인율 하락을 추론하지 않습니다.

## 03. Why Value Alone May Fail

**원문 (p17 「코스피 아웃퍼폼의 조건」, p18)** — 단일 가치·성장 스타일의 한계와 시장 반응을 다룹니다.

**우리의 구현** — [연간 백테스트](src/vfs_research/backtest.py)에서 같은 G·BE 적격기업, 같은 형성일과 수익률 데이터로 저PBR Value를 만들었습니다. Value는 시총가중이며 VFS와 다르게 상한을 추가하지 않았습니다.

**실증 결과** — 아래 표는 실제 공통기간 2021-07~2021-12, 월 N=6, 배당 미포함 gross 0bp입니다.

{table}

*CAGR·변동성·Sharpe·Sortino는 월자료를 연환산한 6개월 진단치입니다. 장기 기대수익률을 의미하지 않습니다. MDD는 첫 투자 직전 NAV=1을 포함합니다.*

**판정: ADAPTED.** 이 표로 원문 2016-2026년 가치전략의 부진을 검증했다고 주장할 수 없습니다.

## 04. Rebuilding the VFS Strategy

**원문 (p20 표6, p21 투자규칙)** — PBR×G 네 셀 중 Low-Good과 High-Good을 각각 절반씩 담고, 셀 안의 종목 비중을 25%로 제한합니다.

**우리의 구현** — [분류](src/vfs_research/sorts.py)와 [수렴하는 상한 재배분](src/vfs_research/portfolio.py)을 구현했습니다. 6월 말까지 공개된 연간 자료로 7월 수익률부터 투자하며, PBR 중앙값과 각 PBR군 내부 G 중앙값은 **우리 가정**입니다. 동점은 Low/Bad에 모두 남겨 인위적으로 쪼개지 않았습니다.

**실증 결과** — [연간 셀 기업수](outputs/cell_formation_coverage.csv)와 [형성 비중·거래량](outputs/formation_summary.csv)을 공개했습니다. 25%/12.5%는 형성 시점에 검증했으며, 연중 보유비중의 드리프트는 월별 집계에 별도로 남겼습니다. 결측 보유종목을 사후 제외하면 다른 포트폴리오가 되므로, 해당 연간 경로를 중단했습니다.

![실제 연간 4셀 기업수: 2016~2025년 7월 형성, 수익률 유효성과 별개](outputs/figures/cells.png)

**판정: REIMPLEMENTED 규칙 / ADAPTED 입력.** MSCI의 다차원 점수와 사외이사 비율의 의미는 다릅니다. 원문 완전 재현이 아닙니다. [원문과 구현 구분](docs/ORIGINAL_VS_IMPLEMENTATION.md), [가정](docs/ASSUMPTIONS.md).

## 05. Original Results vs Our Backtest

**원문 (p21 표7·그림37-38, p22 표8-9, p23 표10)** — 원문은 2016.01~2026.04의 배당 포함 VFS 성과와 대형주·성장·가치 혼합 노출을 제시합니다.

**우리의 구현** — 성과·표본·점수·가격/총수익률 차이를 분리했습니다. 종목별 FnGuide 원천과 유료 파생자료는 재배포하지 않았고, 규모·ROE·집중도 집계만 공개했습니다. 원문 편입종목이나 현재 업종을 과거로 소급하지 않았습니다.

**실증 결과**

| 평가항목 | 미래에셋 원문 REFERENCE_ONLY | 우리 OUR_RESULT | 직접 비교 가능성 |
| --- | --- | --- | --- |
| G | MSCI governance score | OpenDART 사외이사/전체 이사 | 정의 다름 |
| 수익률 | 현금배당 포함, 윈저화 | PRICE_RETURN_ONLY; 기존 가격필터 미해결 | 제한 |
| 기간/표본 | 2016.01~2026.04, MSCI 커버리지 | 2021.07~12, 6개월; 전체 PIT 결합 782기업 | 불일치 |
| VFS | 연평균 20.14%, Sharpe 0.75 | 6개월 누적 {pct(r.loc['VFS','total_return'])}, Sharpe {r.loc['VFS','sharpe']:.2f}* | 동일 재현 아님 |
| Value | 연평균 12.63%, Sharpe 0.50 | 6개월 누적 {pct(r.loc['Value','total_return'])}, Sharpe {r.loc['Value','sharpe']:.2f}* | 우리 내부 쌍별 비교 |
| KOSPI | 연평균 18.10%, Sharpe 0.66 | 6개월 누적 {pct(r.loc['Market','total_return'])} | 불일치 |
| FF3 α / HAC p / CI | 표7에 없음 | NOT_ESTIMATED (6<24개월) | OUR EXTENSION |

*원문 연평균수익률의 정확한 산식은 확인되지 않아 CAGR로 바꾸지 않았습니다. 원문 연평균과 우리 6개월 누적값은 다른 기간·정의의 지표입니다. 수치를 나란히 둔 목적은 일치나 우위 주장이 아니라 비교 불가능한 이유를 드러내는 것입니다.*

![Figure 1 실제 공통기간 누적지수: 2021-07~12 N=6 PRICE_RETURN_ONLY gross 0bp](outputs/figures/cumulative.png)

**Figure 2 - FF3 α와 95% CI: NOT_ESTIMATED.** 표본이 부족하므로 숫자나 모의 오차막대를 그리지 않았습니다. [알파 상태 CSV](outputs/ff3_alphas.csv).

**판정: ADAPTED / NOT_ESTIMATED.** VFS의 누적손실이 Value보다 작다는 진단과, 거버넌스의 독립적 보상은 다른 주장입니다.

## 06. Alpha, Regimes & Robustness

**원문 (p28 「밸류 포커스 스타일 다기간 검증」, 그림40-42)** — 연도별 롱/롱숏 수익률과 Sharpe를 비교하며, Sharpe 그림은 RF 2%를 가정합니다.

**우리의 구현 - OUR EXTENSION** — FF3 세 회귀(VFS, Value, VFS−Value), HAC3/6, 95% CI, 블록 부트스트랩, 비용·가중·상위5 제외·G 컷·PIT 지연·규모중립 민감도를 사전 고정했습니다. spread에서 RF를 다시 차감하지 않습니다. 미완성 연도에서 결측월만 빼고 연간 수익률을 계산하지 않습니다.

이 절의 FF3는 보조 위험조정 검정입니다. 주 작업인 VFS 구성·가중·리밸런싱·원수익 백테스트는 SMB/HML 자료 없이도 실행됩니다. α·t·p·CI는 최소 24개월 미충족으로 NOT_ESTIMATED이며, 이는 VFS 원수익이 존재하지 않는다는 뜻이 아닙니다.

| 원문 다기간 분석 | 우리 독립 검증 | 결과 |
| --- | --- | --- |
| 연도별 롱/롱숏 수익률 | [연간 수익률 상태](outputs/annual_returns.csv) | VFS 완전한 12개월 연도 없음 |
| 연도별 Sharpe | 12개월 rolling volatility | NOT_ESTIMATED; 공통 6개월 |
| 표7 원수익·위험지표 | [FF3 및 spread HAC](outputs/ff3_alphas.csv) | α/t/p/CI 모두 NA |
| 다기간 성과 | [등록된 11개 민감도](outputs/robustness.csv) | 모든 사양/NA 공개; 알파 미추정 |
| 독립 OOS 미제시 | Independent OOS - NOT VERIFIED | UNVERIFIED; 기존 연구 이력으로 전 기간 인지 |

![실제 동일 6개월 민감도 월평균 spread: 가격수익률, 비용 사양 별도, 추론 CI 없음](outputs/figures/robustness.png)

**실증 결과** — [편향 감사](outputs/bias_audit.csv)와 [블록 부트스트랩](outputs/bootstrap.json)은 해결한 절차와 남은 자료 제약을 나눕니다. 생존·상폐·기업행동·배당·역사적 업종·법정 규모요건·독립 OOS는 미검증입니다. Holm 보정에 투입할 추정 가능한 알파 검정도 없습니다.

[ROE·12-1 가격 모멘텀 노출 진단](outputs/control_exposure_diagnostics.csv)은 형성 이전 자료만 쓰며, 각 변수의 관측 비중을 함께 표시합니다. 이는 빠진 산업·배당·유동성 통제를 해결한 인과 검정이 아닙니다. EW 사양에서는 같은 6개월의 VFS−Value 월평균 차이가 음수로 바뀌어, 성과 차이의 규모·가중 방식 의존성도 남았습니다.

**판정: NOT_ESTIMATED / OOS NOT VERIFIED.** 실패한 검증 게이트는 전략 실패의 확정도, 알파 부재의 확정도 아닙니다. 현재 자료로는 질문에 통계적으로 답할 수 없습니다.

## 07. What Held Up, What Did Not

**원문 (p25 「결론: 멀티플 탈출의 조건」)** — 가격 수준보다 거버넌스와 이익이 뒷받침하는 가치의 이유를 강조합니다.

**우리의 구현** — 투자규칙을 공시 시점에 맞춰 번역하고, 실제 보유경로가 어디서 끊기는지 확인했습니다. 원문과 같은 성과를 얻기 위해 표본이나 조건을 바꾸지 않았습니다.

**실증 결과** — {brief} 원본에서 절대 가격수익률 100% 초과 659건을 제거한 사실도 다시 확인했습니다. 배당과 상폐 대가, 수정주가·공시 정정 이전 값, 역사적 모집단을 확보해야 검증을 진전시킬 수 있습니다.

**판정: EMPIRICAL_LIMITED.** 규칙과 데이터 연결은 재구현했지만, 투자 가능한 장기 전략·유의한 FF3 알파·거버넌스 인과효과는 입증하지 못했습니다. 다음 분석은 같은 설계를 유지한 완전한 기업행동·총수익률 자료와 충분한 신규 독립기간에서 수행해야 합니다.

## Appendix A. Scope of Replication

p26 자기자본비용 추정과 p27 MSCI 다차원 점수·요인 계산(그림39)은 **NOT_REPLICATED**입니다. FF3는 우리 조건부 위험조정 확장입니다. 원문 목차와 정확한 페이지는 [근거 매핑](docs/REPORT_TO_IMPLEMENTATION_MAP.md)에 있습니다.

## Prior Research & Limitations

[기존 거버넌스 탐색연구](legacy_governance_pilot/output/RESEARCH_NOTE.md)와 [비유의 보조 결과](legacy_governance_pilot/output/RESULT_STATUS.json)는 이관해 보존했습니다. 과거 고정150단계 표본의 2024.04~2026.03 24개월 α +0.5145%/월, HAC p=0.3888(비유의)은 **LEGACY_ONLY**이며 새 VFS 실적이 아닙니다. 기존 전수 4셀 주 검정은 연속 3개월로 미추정이었습니다. [연구 이력](docs/LEGACY_HISTORY.md), [이관 명세](docs/MIGRATION_MANIFEST.md).

## Methods / Reproducibility / Data Dictionary / Limitations

[방법과 가정](docs/ASSUMPTIONS.md) · [실행·공개 숫자 재계산](docs/REPRODUCIBILITY.md) · [데이터 사전](docs/DATA_DICTIONARY.md) · [게이트 A](docs/GATE_A.md) · [편향 감사](outputs/bias_audit.csv) · [이관 상태](MIGRATION_STATUS.md).
''',brief,summary


def report():
    d,_,_,_=public_inputs();export_strategy_diagnostics(d)
    text,brief,summary=narrative()
    (ROOT/'README.md').write_text(text)
    (ROOT/'outputs/public_result_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    report=text.replace('](reports/','](').replace('](docs/','](../docs/').replace('](outputs/','](../outputs/').replace('](src/','](../src/').replace('](legacy_','](../legacy_').replace('](config/','](../config/').replace('](dashboard/','](../dashboard/').replace('](MIGRATION_STATUS.md)','](../MIGRATION_STATUS.md)')
    (ROOT/'reports/RESEARCH_REPORT.md').write_text(report)
    (ROOT/'reports/EXECUTIVE_BRIEF.md').write_text('# Value Focus Style - Executive Brief\n\n독립 개인 Quant/ESG 연구 · EMPIRICAL_LIMITED · OUR_RESULT\n\n'+strategy_brief()+'\n\n'+brief+'\n\n'+performance_table(pd.read_csv(ROOT/'outputs/performance_summary.csv'))+'\n\n표의 기간: 2021-07~2021-12, N=6개월, PRICE_RETURN_ONLY, gross 0bp. VFS 자체의 8개월 기록은 별도 분석입니다. CAGR/Sharpe는 짧은 기간의 연환산 진단치. MSCI G를 사외이사 비율로 대체했으며, 배당·상폐·역사적 유니버스·독립 OOS 미검증입니다. 결측 이후 연간 경로 중단은 우리의 보수적 구현 가정입니다. FF3는 보조 검정이고 표본 부족으로 미추정입니다.\n\n'+f'[상세 보고서](RESEARCH_REPORT.pdf) · [신규 연구]({REPO}) · [공식 원문]({SOURCE})\n')
    d,q,perf,s=public_inputs();table=performance_table(perf)
    tr=''.join('<tr>'+''.join('<td>'+html.escape(v)+'</td>' for v in [r.strategy,pct(r.total_return),pct(r.mdd),f'{r.sharpe:.2f}'])+'</tr>' for r in perf.itertuples())
    panels=''.join(f'<section><h2>{title}</h2><img src="{name}.svg" alt="{html.escape(title)} - OUR_RESULT, PRICE_RETURN_ONLY, 기간과 단위는 그림 하단" loading="lazy"></section>' for name,title in [('vfs_observed','VFS 자체의 보유경로: 연속 8개월'),('cumulative','Value·시장 비교: 공통 6개월'),('spread','월별 VFS−Value 차이'),('drawdown','월간 Drawdown'),('coverage','원문 기간과 실제 자료 커버리지'),('cells','연간 4셀 형성 기업수'),('robustness','강건성: 기술통계만 산출'),('size_G','규모와 G 프록시의 혼동')])
    page=f'''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VFS 독립 검증 | EMPIRICAL_LIMITED</title><style>body{{font:16px/1.7 system-ui,'Apple SD Gothic Neo','Malgun Gothic',sans-serif;background:#f5f7fa;color:#172033;margin:0}}main{{max-width:1020px;margin:auto;padding:28px 20px}}h1{{line-height:1.3;font-size:clamp(26px,4vw,40px)}}section{{background:white;padding:22px;margin:24px 0;border-radius:10px}}img{{width:100%;height:auto}}.status{{background:#fff3d4;padding:15px;border-left:4px solid #b76c14}}table{{width:100%;border-collapse:collapse}}th,td{{text-align:right;padding:8px;border-bottom:1px solid #dae0e8}}th:first-child,td:first-child{{text-align:left}}a{{color:#1856ae}}.scroll{{overflow:auto}}@media(max-width:600px){{section{{padding:14px}}th,td{{font-size:14px}}}}</style><main><p>독립 개인 연구 · OUR_RESULT</p><h1>Value Focus Style<br>공시 기반 거버넌스 가치전략의 검증</h1><p>VFS의 Value 대비 성과 차이는 거버넌스의 증분인가, 기존 스타일 노출인가?</p><div class="status"><strong>EMPIRICAL_LIMITED · 전체 실증 미완료</strong><p>{brief.replace('**','')}</p><p>MSCI 점수 대신 사외이사 비율. PRICE_RETURN_ONLY / gross 0bp. 배당·상폐·독립 OOS 미검증. CAGR/Sharpe는 6개월의 연환산 진단치.</p></div><p><a href="{REPO}">Narrative README</a> · <a href="{REPO}/blob/main/reports/RESEARCH_REPORT.pdf">연구 PDF</a> · <a href="{SOURCE}">미래에셋 원문</a> · <a href="monthly_returns.csv">공개 월별 CSV</a></p><section><h2>실제 성과: 2021-07~12, N=6개월</h2><div class="scroll"><table><thead><tr><th>전략</th><th>누적</th><th>MDD</th><th>Sharpe*</th></tr></thead><tbody>{tr}</tbody></table></div></section>{panels}<section><h2>Figure 2: FF3 α · 95% CI</h2><p>NOT_ESTIMATED - 6개월 &lt; 최소 24개월. α, t, p, CI, factor beta와 12개월 rolling volatility는 NA입니다. 모의 결과로 대체하지 않았습니다.</p><h2>Independent OOS - NOT VERIFIED</h2><p>과거 G 연구를 이미 알고 설계했으며 충분한 신규 독립 기간이 없습니다.</p><p>이전 보조 FF3 G 알파는 LEGACY_ONLY이며 새 VFS 성과가 아닙니다.</p><a href="{REPO}/blob/main/outputs/bias_audit.csv">편향 감사 전체</a></section><footer>모든 OUR_RESULT 숫자는 동일한 공개 monthly_returns.csv에서 계산. 원문 표7 수치는 REFERENCE_ONLY. 투자 실행 가능성과 인과효과는 미검증.</footer><script id="result-data" type="application/json">{json.dumps(summary,ensure_ascii=False)}</script></main></html>'''
    page=page.replace('VFS의 Value 대비 성과 차이는 거버넌스의 증분인가, 기존 스타일 노출인가?','실제 공시시점 자료로 구성한 VFS의 수익률·위험·보유경로는 어떠한가?')
    page=page.replace('EMPIRICAL_LIMITED · 전체 실증 미완료','VFS 백테스트 · 부분 관측 / EMPIRICAL_LIMITED')
    page=page.replace('<p>'+brief.replace('**','')+'</p>','<p>'+strategy_brief()+'</p><p>'+brief.replace('**','')+'</p>')
    page=page.replace('<h2>Figure 2: FF3 α · 95% CI</h2>','<h2>보조 검정: FF3 α · 95% CI</h2>')
    (ROOT/'dashboard/index.html').write_text(page)
    import shutil
    for p in (ROOT/'outputs/figures').glob('*.svg'):shutil.copy2(p,ROOT/'dashboard'/p.name)
    shutil.copy2(ROOT/'outputs/monthly_returns.csv',ROOT/'dashboard/monthly_returns.csv')
    from .pdf_report import build_pdf
    build_pdf()
    print('README_REPORT_DASHBOARD_GENERATED_FROM_PUBLIC_RESULTS')


def verify_public():
    d,q,perf,s=public_inputs()
    if not np.allclose(d.spread,d.VFS-d.Value,equal_nan=True):raise ValueError('spread arithmetic')
    from .stats import contiguous
    if not contiguous(q):raise ValueError('noncontiguous primary')
    for row in perf.to_dict('records'):
        actual=performance(q,row['strategy'])
        for col in ['total_return','cagr','volatility','sharpe','sortino','mdd']:
            if not np.isclose(row[col],actual[col],equal_nan=True):raise ValueError('public metric drift '+col)
    ff=pd.read_csv(ROOT/'outputs/ff3_alphas.csv')
    if len(q)<24 and (ff.status.ne('NOT_ESTIMATED').any() or ff[['alpha','t_hac','p_hac','ci_low','ci_high']].notna().any().any()):raise ValueError('unsupported alpha inference')
    summary=result_summary();published=json.loads((ROOT/'outputs/public_result_summary.json').read_text())
    if published!=summary:raise ValueError('summary mismatch')
    page=(ROOT/'dashboard/index.html').read_text();embedded=json.loads(re.search(r'<script id="result-data" type="application/json">(.*?)</script>',page,re.S).group(1))
    if embedded!=summary:raise ValueError('dashboard numbers differ')
    own=vfs_strategy_summary(d);stored=pd.read_csv(ROOT/'outputs/vfs_strategy_summary.csv')
    for name in ['VFS','Market']:
        a=own.set_index('strategy').loc[name];b=stored.set_index('strategy').loc[name]
        for key in ['total_return','cagr','volatility','sharpe','sortino','mdd']:
            if not np.isclose(a[key],b[key],equal_nan=True):raise ValueError('VFS own-path metric mismatch')
    _,brief,_=narrative()
    for p in ['README.md','reports/RESEARCH_REPORT.md','reports/EXECUTIVE_BRIEF.md','dashboard/index.html']:
        content=(ROOT/p).read_text()
        if brief.replace('**','') not in content.replace('**',''):raise ValueError('narrative mismatch '+p)
    # Local Markdown and HTML links must resolve; external URLs separately checked during publication.
    broken=[]
    for p in [ROOT/'README.md',ROOT/'reports/RESEARCH_REPORT.md',ROOT/'reports/EXECUTIVE_BRIEF.md',ROOT/'dashboard/index.html']:
        content=p.read_text();links=re.findall(r'\]\(([^)]+)\)|(?:href|src)="([^"]+)"',content)
        for pair in links:
            link=next(v for v in pair if v)
            if link.startswith(('https:','http:','#')):continue
            if not (p.parent/link.split('#')[0]).exists():broken.append(str(p.relative_to(ROOT))+':'+link)
    if broken:raise ValueError('dead local links: '+str(broken))
    plan=ROOT/'config/vfs_pre_analysis_plan.yaml'
    if digest(plan)!=json.loads((ROOT/'config/design_lock.json').read_text())['sha256']:raise ValueError('plan lock mismatch')
    manifest=pd.read_csv(ROOT/'docs/migration_manifest.csv').fillna('')
    copied=manifest.loc[manifest.action.eq('COPY')]
    for row in copied.itertuples():
        if digest(ROOT/row.target)!=row.sha256:raise ValueError('migration changed '+row.target)
    forbidden=[]
    for p in ROOT.rglob('*'):
        if not p.is_file() or any(z in p.relative_to(ROOT).parts for z in ['.git','.cache','private','raw','__pycache__','.pytest_cache']):continue
        if p.suffix in ['.parquet','.bundle']:forbidden.append(str(p.relative_to(ROOT)))
        if p.suffix in ['.py','.md','.json','.csv','.yaml','.yml','.html']:
            content=p.read_text(errors='replace')
            if re.search(r'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|crtfc_key=[A-Za-z0-9]{20,})',content):raise ValueError('potential exposed credential: '+str(p.relative_to(ROOT)))
    if forbidden:raise ValueError('raw/proprietary publication '+str(forbidden))
    if {'SMB','HML','Mkt-RF'} & set(d.columns):raise ValueError('factor columns belong to supplementary inputs, not the VFS raw-return file')
    result={'status':'PASS','research_focus':'VFS_PORTFOLIO_BACKTEST','actual_months':len(q),'paired_comparison_months':len(q),'vfs_own_months':len(vfs_observed_window(d)),'copied_files_hash_verified':len(copied),'performance_recomputed':True,'narrative_dashboard_same_results':True,'local_link_failures':0,'secret_scan':'PASS','source_rows_published':False,'empirical_completion':'EMPIRICAL_LIMITED'}
    (ROOT/'outputs/public_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
