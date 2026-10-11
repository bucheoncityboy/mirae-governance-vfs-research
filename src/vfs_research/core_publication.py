"""Hypothesis-first publication from approved real aggregates only."""
import argparse
import html
import json
import re
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from .data_ingest import ROOT, digest
from .core_hypotheses import paired_description, CELLS

REPO = "https://github.com/bucheoncityboy/mirae-governance-vfs-research"
PAGES = "https://bucheoncityboy.github.io/mirae-governance-vfs-research/"


def inputs(root=ROOT):
    root = Path(root)
    out = root / "outputs/core_hypotheses"
    return json.loads((out / "hypothesis_results.json").read_text()), pd.read_csv(out / "cell_monthly_returns.csv", parse_dates=["date"])


def hypothesis_table(r):
    h1, h2, h3 = r["H1_low_pbr_governance"], r["H2_high_pbr_governance"], r["H3_strategy"]
    return [
        ["핵심 가설", "비교군", "결과", "실증 판정"],
        ["H1 가치 함정 구분", "Low-Good vs Low-Bad", f"{h1['months']}개월 누적 {h1['good_cumulative_pct']:+.2f}% / {h1['bad_cumulative_pct']:+.2f}%; 월평균 차이 {h1['mean_monthly_good_minus_bad_pp']:+.4f}%p", h1["judgment"]],
        ["H2 고PBR 선별", "High-Good vs High-Bad", f"{h2['months']}개월 누적 {h2['good_cumulative_pct']:+.2f}% / {h2['bad_cumulative_pct']:+.2f}%; 월평균 차이 {h2['mean_monthly_good_minus_bad_pp']:+.4f}%p", h2["judgment"]],
        ["H3 VFS 포트폴리오", "VFS vs Value / G-neutral / KOSPI", f"Value 공통 6개월 -11.14% / -13.72%; 월평균 차이 {h3['vfs_minus_value']['mean_monthly_good_minus_bad_pp']:+.4f}%p; EW -0.4158%p", h3["judgment"]],
    ]


def md_table(rows):
    return "\n".join(["| " + " | ".join(map(str, rows[0])) + " |", "| " + " | ".join(["---"] * len(rows[0])) + " |"] + ["| " + " | ".join(map(str,row)) + " |" for row in rows[1:]])


def loss_summary(root=ROOT):
    d = pd.read_csv(Path(root) / "outputs/core_hypotheses/forward_loss_12m.csv")
    rows = [["셀", "형성 기업·연도", "완전한 12개월 경로", "우측 검열", "결측/비정상", "-30% 이하 손실(완전 경로)"]]
    for cell in CELLS:
        q=d.loc[d.cell.eq(cell)]
        n=int(q.complete_12m_n.sum());loss=int(q.loss_30pct_n.sum())
        rows.append([cell,int(q.formation_n.sum()),n,int(q.right_censored_n.sum()),int(q.missing_or_invalid_path_n.sum()),f"{loss}/{n} ({loss/n*100:.2f}%)" if n else "NOT_TESTED"])
    return rows


def sections(root=ROOT):
    root=Path(root);r,cells=inputs(root)
    h1,h2,h3=r["H1_low_pbr_governance"],r["H2_high_pbr_governance"],r["H3_strategy"]
    cross=r["cross_section"]
    f=pd.read_csv(root/'outputs/core_hypotheses/formation_diagnostics.csv',parse_dates=['date'])
    parts=[]
    parts.append(("Executive Summary", "企業의 가치평가(PBR)에 거버넌스 정보를 결합하면 저평가 기업의 가치 함정을 구분하고 고평가 기업을 선별하며 투자 포트폴리오를 개선할 수 있는가?\n\n".replace('企業','기업') + md_table(hypothesis_table(r)) + "\n\nH1은 짧은 가격수익률 비교에서 가설 방향과 반대였고, H2는 가설 방향과 같았습니다. 두 표본 모두 24개월 최소기간에 못 미쳐 경제적 가설 판정은 INSUFFICIENT_EVIDENCE입니다. H3는 Value 대비 양수 차이가 동일가중에서 음수로 바뀌어 MIXED_EVIDENCE입니다. 미추정은 통계적으로 비유의한 결과나 효과 0과 다릅니다.\n\n새 기여는 네 셀의 실제 보유경로, 셀별 결측 감사, 형성 특성, 관측 단면 및 12개월 후속 가격 손실을 계산한 것입니다. 이는 기존 결과를 알고 구성한 탐색적 확장입니다."))
    parts.append(("Research Design", "기존 적격기업을 7월에 형성합니다. 6월 말까지 공개된 G·장부자본과 lagged ME로 PBR 중앙값을 나누며 동점은 Low, 각 PBR군의 G 중앙값 동점은 Bad입니다. G는 사외이사/전체 이사 비율이며 원문의 MSCI 거버넌스 점수와 다릅니다.\n\n네 셀은 형성 시 시가총액 가중 및 종목 25% 상한을 적용합니다. VFS는 Low-Good 50% + High-Good 50%로 최종 종목 상한 12.5%를 유지합니다. 형성 후에는 연간 보유와 비중 드리프트를 적용합니다. 보유수익률 하나라도 결측이면 해당 셀의 연간 경로를 다음 형성까지 중단하며 결측을 채우거나 재선정하지 않습니다.\n\n모든 실측 수익률은 PRICE_RETURN_ONLY, gross 0bp입니다. 각 가설의 가장 긴 공통 연속기간을 독립적으로 보고합니다. 단면 탐색은 최초 형성의 구성원을 계속 추적해 관측된 종목 수익률만 요약하므로 투자 가능한 NAV가 아닙니다.\n\n" + f"원천 G {r['source_validation']['governance_verified']:,}건·재무 {r['source_validation']['financial_verified']:,}건·증빙 객체 {r['source_validation']['raw_objects_rehashed']:,}개를 재검증했습니다. PIT 결합 {r['source_validation']['joint_companies']}기업·{r['source_validation']['joint_observations']:,}개 적격 주식-월입니다. 원문 2016–2020년의 결합 PIT 공백은 남습니다. 기존 분석계획과 해시는 보존했습니다."))
    for label,h,group in [("H1 — Does Governance Differentiate Value Traps?",h1,"Low"),("H2 — Does Governance Differentiate High-PBR Firms?",h2,"High")]:
        cc=cross['groups'][group]
        s=f"**{h['start']}~{h['end']}, 공통 {h['months']}개월.** Good {h['good_cumulative_pct']:+.4f}%, Bad {h['bad_cumulative_pct']:+.4f}%, 월평균 Good−Bad {h['mean_monthly_good_minus_bad_pp']:+.4f}%p. 차이가 양수인 월 {h['positive_spread_months']}/{h['months']}, 음수인 월 {h['negative_spread_months']}/{h['months']}입니다.\n\n"
        s+=md_table([["표본 단위","Good","Bad"],["같은 기간 형성 기업 수",h['formation_companies_by_cell'][h['good']],h['formation_companies_by_cell'][h['bad']]],["같은 기간 보유 기업-월",h['matched_held_security_months'][h['good']],h['matched_held_security_months'][h['bad']]]])
        date=pd.Timestamp(h['start']);z=f.loc[f.date.eq(date)&f.cell.isin([h['good'],h['bad']])].set_index('cell')
        s+='\n\n'+md_table([["형성 특성 (관측 종목 평균)","Good","Bad"],["PBR 중앙값",f"{z.loc[h['good'],'pbr_median']:.3f}",f"{z.loc[h['bad'],'pbr_median']:.3f}"],["시총 중앙값 (십억원)",f"{z.loc[h['good'],'lag_me_median']/1e6:.2f}",f"{z.loc[h['bad'],'lag_me_median']/1e6:.2f}"],["ROE 평균 / 가용 기업",f"{z.loc[h['good'],'roe_mean']*100:.2f}% / {int(z.loc[h['good'],'roe_observed_n'])}",f"{z.loc[h['bad'],'roe_mean']*100:.2f}% / {int(z.loc[h['bad'],'roe_observed_n'])}"]])
        s+=f"\n\n별도 관측 단면은 {cc['months']}개월의 월별 종목 평균을 비교했습니다. 월평균 Good−Bad {cc['mean_monthly_good_minus_bad_pp']:+.4f}%p, 양수 월 {cc['positive_months']}, 음수 월 {cc['negative_months']}. 월평균 결측률은 Good {cc['mean_missing_fraction_good_pct']:.3f}%, Bad {cc['mean_missing_fraction_bad_pct']:.3f}%입니다. 모든 월을 투자 가능한 셀 수익률로 연결한 결과가 아닙니다. 규모 3분위·형성연도·PIT ROE별 결과와 PBR 분포는 별도 집계 CSV로 공개합니다.\n\n"
        if group=='Low':
            loss=cross['forward_loss_price_proxy']['Low']
            s+="탐색적 가치 함정 결과변수는 형성 후 12개월 가격 누적손실 ≤-30%입니다. 모든 12개월 수익률을 관측한 종목만 계산하며 결측과 2025년 형성군의 우측 검열을 별도 보고합니다. 종목 생존·기업행동 선택편향 때문에 가치 함정을 회피했다는 인과 결론은 내리지 않습니다. 후속 수익성 악화는 독립 검증된 일관된 재무 시계열이 없어 NOT_TESTED입니다.\n\n"+md_table(loss_summary(root))+f"\n\nLow-Good 손실률은 완전 경로 {loss['Good']['loss_security_years']}/{loss['Good']['complete_security_years']} ({loss['Good']['loss_fraction']*100:.2f}%), Low-Bad는 {loss['Bad']['loss_security_years']}/{loss['Bad']['complete_security_years']} ({loss['Bad']['loss_fraction']*100:.2f}%)입니다. 2021–2024년의 4개 형성군 모두 Good의 손실률이 더 높아 이 가격손실 대리지표도 가치 함정 회피를 뒷받침하지 않았습니다. 이는 독립 기업 N에 대한 유의성 검정이 아니며 재무 악화·경제적 상폐 손실을 포괄하지 않습니다.\n\n관측된 가장 긴 Low-PBR 비교는 Good가 열위였습니다. 다만 6개월 방향을 장기 가치 함정 가설의 기각이나 비유의 검정으로 해석하지 않습니다."
        else:
            s+="Good의 양수 차이는 고PBR군 내부의 관측된 가격수익률 정보입니다. PBR·규모·ROE 차이와 단면 선택편향이 남으며, 적정 PBR이나 자기자본비용(COE)의 인과적 정당화는 검정하지 않았습니다. H1의 2021년 결과와 H2의 2022년 결과도 같은 시장기간의 효과 크기처럼 비교하지 않습니다."
        s+="\n\n판정: **INSUFFICIENT_EVIDENCE**. FF3·HAC3/6·95% CI는 **NOT_ESTIMATED**."
        parts.append((label,s))
    perf=pd.read_csv(root/'outputs/performance_summary.csv')
    neutral=h3['vfs_minus_g_neutral']
    h3text="기존 VFS 결과와 주 분석은 그대로입니다. VFS 자체 2021-07~2022-02의 8개월 누적 -17.30%와 비교군 공통 6개월은 별도 표본입니다.\n\n"+md_table([["2021-07~12 / N=6","누적","월수익률 연환산 변동성*","MDD"]]+[[q.strategy,f"{q.total_return*100:.2f}%",f"{q.volatility*100:.2f}%",f"{q.mdd*100:.2f}%"] for q in perf.itertuples()])
    h3text+=f"\n\nVFS−Value 월평균 +0.4325%p. PBR 50:50 G-neutral과 VFS의 별도 공통기간은 {neutral['start']}~{neutral['end']}, {neutral['months']}개월이며 누적 {neutral['good_cumulative_pct']:+.4f}% / {neutral['bad_cumulative_pct']:+.4f}%, 월평균 차이 {neutral['mean_monthly_good_minus_bad_pp']:+.4f}%p입니다. 서로 다른 기간의 누적치를 동일 성과 순위로 나열하지 않습니다. *짧은 표본의 연환산 변동성은 진단값입니다.\n\n동일 6개월 동일가중에서는 월평균 차이 -0.4158%p로 부호가 역전됐습니다. 형성연도별 G와 log(ME)의 상관은 0.3945~0.4731입니다. VFS는 Low/High 예산·셀 상한·시총가중이 Value와 달라 순수 G 효과를 분리하지 못합니다. H1/H2의 형성 진단은 PBR 분포·규모·ROE·HHI·유효 종목수·결측률도 기록합니다. G-neutral은 PBR군 예산만 맞춘 비교군이며 연속 PBR와 규모까지 같지 않습니다.\n\n거래비용 10/30bp는 기존 one-way 매수+매도 가정과 회전율에 따른 민감도로 남깁니다. 경로 중단 후 이전 비중이 불명확하면 재형성 비용도 NA입니다. 독립 규모 매칭 전략은 소수 형성군·기업행동·결측 제약으로 추가하지 않았으며 규모 층화는 탐색 단면 진단으로 제공합니다.\n\n판정: **MIXED_EVIDENCE**. Value 대비 제한적 양수 차이와 EW 부호 반전이 공존합니다. 장기 투자성과·거버넌스 증분 알파는 INSUFFICIENT_EVIDENCE이며 FF3 알파는 NOT_ESTIMATED입니다."
    parts.append(("H3 — Does VFS Improve Portfolio Outcomes?",h3text))
    parts.append(("Conclusion & Limitations",f"H1·H2를 실제 원천에서 계산했지만 가치 함정 회피, 정당한 프리미엄, 장기 G 알파를 입증하지 못했습니다. H3의 양수 spread도 가중 방식에 의존했습니다. 연구의 기여는 유리한 결과를 선택하는 데 있지 않고, 비교군·관측기간·결측·혼동요인을 일관되게 검증하는 데 있습니다.\n\n단면 자료는 {cross['firms']}개 고유 기업, {cross['expected_security_months']:,}개 기대 기업-월, {cross['observed_security_months']:,}개 관측 기업-월, {cross['calendar_months']}개 달, {cross['annual_formation_cohorts']}개 연간 형성군입니다. 반복 기업-월을 독립 표본으로 취급하지 않습니다. 월 고정효과·Good·log(ME)·연속 PBR·PIT ROE의 기업/형성군 이중 군집 검정 코드를 구현했지만 형성군 5개가 사양의 최소 10개에 못 미쳐 실제 계수·p·CI는 미추정입니다. 58개월의 선택된 단면을 58개월 투자 가능한 전략으로 바꾸거나 FF3의 24개월 조건을 우회하지 않았습니다.\n\n2016–2020년 PIT 공백, 원문 MSCI G와의 차이, 배당·상폐 대가·기업행동, 전체 역사적 모집단, 정정 이전 공시, 독립 OOS는 미검증입니다. 기존 보유 결측 11개 사건에 대해 16개 접수번호·37개 공식 본문 절을 조사했으나 경제적 수익률 수정은 0건입니다. 2021년 12월 권리 전환과 형성 전 거래정지 때문에 관측 가격 NAV의 투자 가능성도 확정하지 못했습니다.\n\n추정 가능한 셀·spread의 HAC3/6 총 16개 사양에는 Holm 보정을 적용하는 코드가 있고 이번에는 전부 미추정입니다. 단면 2개 계수 검정은 별도 탐색 가족으로 관리합니다. 개별 95% CI를 동시 신뢰구간으로 주장하지 않습니다."))
    parts.append(("Appendix", "원문의 목차별 해설과 기존 실증·감사를 보존한 [이전 메인 보고서](snapshots/pre-core-hypotheses-f0cf8db/reports/RESEARCH_REPORT.pdf), [기존 README](snapshots/pre-core-hypotheses-f0cf8db/README.md), [기술 감사 대시보드](dashboard/appendix.html)를 함께 제공합니다.\n\n" + md_table([["보존 자료","문서"],["원문 목차·개혁·반도체·COE/적정 멀티플","[원문 대응표](docs/REPORT_TO_IMPLEMENTATION_MAP.md) · [원문/구현 차이](docs/ORIGINAL_VS_IMPLEMENTATION.md)"],["과거 공시·PIT·원천 재구축·SHA256","[재구축](docs/PUBLIC_SOURCE_REBUILD.md) · [원천 영수증](outputs/reconstruction/recollected_input_manifest.json)"],["기업행동·상폐·11개 결측 사건","[경제적 수익률 감사](docs/ECONOMIC_RETURN_RECOVERY.md) · [수정 0건](outputs/final/return_repair_status.csv)"],["FF3·강건성·설계 잠금·기존 결과","[설계](config/vfs_pre_analysis_plan.yaml) · [강건성](outputs/robustness.csv) · [불변성 목록](docs/core_baseline_hashes.json)"],["신규 탐색 계획·의사결정·재현","[계획](config/core_hypotheses_exploratory_plan.yaml) · [이력](docs/CORE_DECISIONS.md) · [재현](docs/CORE_REPRODUCIBILITY.md)"]]) + f"\n\n[핵심 집계 JSON](outputs/core_hypotheses/hypothesis_results.json) · [면접 요약](docs/INTERVIEW_BRIEF.md) · [연구 PDF](reports/RESEARCH_REPORT.pdf) · [Executive Brief](reports/EXECUTIVE_BRIEF.pdf) · [GitHub Pages]({PAGES})"))
    return parts


def charts(root=ROOT):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    root=Path(root);r,cells=inputs(root);out=root/'outputs/core_hypotheses/figures';out.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.hashsalt':'vfs-core-20261011','axes.spines.top':False,'axes.spines.right':False})
    def save(fig,name):
        fig.subplots_adjust(bottom=.22)
        fig.savefig(out/(name+'.svg'),bbox_inches='tight',metadata={'Date':None})
        svg=out/(name+'.svg')
        svg.write_text(''.join(line.rstrip()+'\n' for line in svg.read_text().splitlines()))
        fig.savefig(out/(name+'.png'),dpi=170,bbox_inches='tight',metadata={'Software':'VFS Research'})
        plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4.7));ax.set_xlim(0,2);ax.set_ylim(0,2);ax.axis('off')
    for x,y,title,desc,color in [(0,1,'Low-Good','H1 Good | VFS 50%','#d8e8fa'),(1,1,'Low-Bad','H1 control','#ffe8d2'),(0,0,'High-Good','H2 Good | VFS 50%','#d8e8fa'),(1,0,'High-Bad','H2 control','#ffe8d2')]:
        ax.add_patch(Rectangle((x+.025,y+.08),.95,.8,facecolor=color,edgecolor='white'))
        ax.text(x+.5,y+.59,title,ha='center',fontsize=18,weight='bold');ax.text(x+.5,y+.32,desc,ha='center',fontsize=12)
    ax.set_title('PBR x outside-director ratio | Original July PIT formation',pad=12,weight='bold')
    fig.text(.5,.02,'Median ties: PBR -> Low; G -> Bad | Cell formation cap 25%; VFS stock cap 12.5%',ha='center',fontsize=9);save(fig,'structure')
    for label,key,good,bad in [('h1','H1_low_pbr_governance',*CELLS[:2]),('h2','H2_high_pbr_governance',*CELLS[2:])]:
        h=r[key];q=cells.loc[cells.date.between(h['start'],h['end'])];dates=[q.date.iloc[0]-pd.offsets.MonthBegin(1)]+q.date.tolist()
        fig,ax=plt.subplots(figsize=(9,4.5))
        for c,color in [(good,'#1765a5'),(bad,'#ce7132')]:
            nav=np.r_[100,100*(1+q[c]).cumprod()];ax.plot(dates,nav,marker='o',label=f'{c}: {nav[-1]/100-1:+.2%}',color=color,lw=2)
        ax.axhline(100,color='#8994a3',lw=.8);ax.set_ylabel('Price NAV (initial = 100)');ax.legend();ax.grid(alpha=.15)
        ax.set_title(f"{label.upper()} | {h['start']} to {h['end']} | {h['months']} identical consecutive months",weight='bold')
        fig.autofmt_xdate();fig.text(.5,.01,f"Observed capped-VW cells | Gross 0bp | PRICE_RETURN_ONLY | FF3 NOT_ESTIMATED | Positive spread {h['positive_spread_months']}/{h['months']}",ha='center',fontsize=8);save(fig,label)
    fig,axes=plt.subplots(1,2,figsize=(11,4.4))
    baseline=pd.read_csv(root/'outputs/monthly_returns.csv',parse_dates=['date']);q=baseline.loc[baseline.primary_window]
    for c,color in [('VFS','#1765a5'),('Value','#ce7132'),('Market','#536273')]:
        axes[0].plot([q.date.iloc[0]-pd.offsets.MonthBegin(1)]+q.date.tolist(),np.r_[100,100*(1+q[c]).cumprod()],marker='o',label=c,color=color)
    n=pd.read_csv(root/'outputs/reconstruction/exploratory_g_neutral_monthly.csv',parse_dates=['date']);h=r['H3_strategy']['vfs_minus_g_neutral'];n=n.loc[n.date.between(h['start'],h['end'])]
    for c,color in [('VFS','#1765a5'),('GNeutral','#6b6eaa')]:
        axes[1].plot([n.date.iloc[0]-pd.offsets.MonthBegin(1)]+n.date.tolist(),np.r_[100,100*(1+n[c]).cumprod()],marker='o',label=c,color=color)
    for ax,title in zip(axes,['VFS / Value / KOSPI: 2021-07 to 12, N=6',f"Separate PBR-budget control: {h['start']} to {h['end']}, N=2"]):
        ax.set_title(title,fontsize=10);ax.legend();ax.grid(alpha=.15);ax.tick_params(axis='x',rotation=35);ax.set_ylabel('Price NAV (initial = 100)')
    fig.suptitle('H3 | Each panel uses its own common continuous window',weight='bold');fig.text(.5,-.02,'PRICE_RETURN_ONLY | Gross 0bp | Different panels are not a same-period ranking | FF3 NOT_ESTIMATED',ha='center',fontsize=9);save(fig,'h3')
    fig,ax=plt.subplots(figsize=(9,4));values=[r['H3_strategy']['vfs_minus_value']['mean_monthly_good_minus_bad_pp'],r['H3_strategy']['equal_weight_vfs_minus_value_monthly_pp']]
    ax.barh(['Capped market-cap VFS vs Value','Equal-weight sensitivity'],values,color=['#1765a5','#ce7132'],height=.5)
    for y,v in enumerate(values):ax.text(v+( .02 if v>0 else -.02),y,f'{v:+.4f} pp',va='center',ha='left' if v>0 else 'right')
    ax.set_xlim(-.7,.7);ax.axvline(0,color='#536273');ax.set_xlabel('Mean monthly VFS minus Value (percentage points)');ax.set_title('H3 sign reversal | Same six months, 2021-07 to 12',weight='bold')
    fig.text(.5,.005,'Weighting, PBR budgets, size and concentration remain confounded | Descriptive only; no error bars',ha='center',fontsize=9);save(fig,'robustness')


def sync(root=ROOT):
    # The focused supplement owns the current research narrative. Preserve the
    # historical publisher for archived runs; do not invoke its PDF path.
    if (Path(root)/'outputs/supplement/summary.json').exists():
        import subprocess
        subprocess.run(['node', str(Path(root)/'node_modules/tsx/dist/cli.mjs'),
                        str(Path(root)/'src/publication.ts')], cwd=root, check=True)
        return
    root=Path(root);r,_=inputs(root);parts=sections(root)
    figures={'Research Design':'structure','H1 — Does Governance Differentiate Value Traps?':'h1','H2 — Does Governance Differentiate High-PBR Firms?':'h2','H3 — Does VFS Improve Portfolio Outcomes?':'h3'}
    text='# VFS: 세 가지 핵심 투자 가설의 실증\n\n독립 개인 Quant/ESG 연구 · 2026-10-11 KST · 탐색적 확장 · PRICE_RETURN_ONLY\n\n'
    for title,content in parts:
        text+='## '+title+'\n\n'+content+'\n\n'
        if title in figures:text+=f"![{title}: 실제 관측기간과 표본은 본문 참조](outputs/core_hypotheses/figures/{figures[title]}.svg)\n\n"
        if title.startswith('H3'):text+='![동일기간 가중 방식의 부호 반전](outputs/core_hypotheses/figures/robustness.svg)\n\n'
    # Exact legacy arithmetic remains visible for existing invariant validator.
    from .reporting import narrative,result_summary
    legacy=narrative()[1]
    text+='기존 주 분석 기준 문구: '+legacy+'\n'
    (root/'README.md').write_text(text)
    report=re.sub(r'\]\(([^)]+)\)',lambda m:']('+ (m[1] if m[1].startswith(('https:','http:','#')) else '../'+m[1])+')',text)
    (root/'reports/RESEARCH_REPORT.md').write_text(report)
    brief='# VFS Executive Brief\n\n'+parts[0][1]+'\n\n'+parts[4][1]+'\n\n'+parts[5][1]+'\n\n기존 주 분석 기준 문구: '+legacy+'\n\n[연구보고서](RESEARCH_REPORT.pdf) · [집계](../outputs/core_hypotheses/hypothesis_results.json)\n'
    (root/'reports/EXECUTIVE_BRIEF.md').write_text(brief)
    docs=re.sub(r'\]\(([^)]+)\)',lambda m:']('+ (m[1] if m[1].startswith(('https:','http:','#')) else '../'+m[1])+')',text)
    (root/'docs/CORE_HYPOTHESES.md').write_text(docs)
    (root/'docs/RESEARCH_CONCLUSION.md').write_text('# 세 가설의 실증 판정\n\n'+parts[0][1]+'\n\n'+parts[5][1]+'\n\n[경제적 수익률 감사](ECONOMIC_RETURN_RECOVERY.md) · [원천 재구축](PUBLIC_SOURCE_REBUILD.md)\n')
    interview='# RA 면접에서 설명할 VFS 연구\n\n'+parts[0][1]+'\n\n'
    interview+=f"실제 PIT 원천에서 네 셀을 구성했습니다. Low-PBR 비교는 월 {r['H1_low_pbr_governance']['mean_monthly_good_minus_bad_pp']:+.4f}%p, High-PBR 비교는 {r['H2_high_pbr_governance']['mean_monthly_good_minus_bad_pp']:+.4f}%p였지만 각각 6개월과 4개월로 기간도 다릅니다. VFS−Value +0.4325%p만 보고 G 효과라고 주장하면 H1과 가중 방식 반전을 설명하지 못합니다.\n\n왜 결측이 작아도 중단하는가? 가격·현금·승계 수량을 검증하지 못하면 투자 가능한 NAV를 알 수 없기 때문입니다. 11개 사건의 16개 접수번호·37개 본문 절을 확인해도 경제적 수정은 0건입니다.\n\n단면 58개월은 58개월 전략 실적이 아닙니다. 결측 없는 관측만 요약한 선택 표본이고, 반복 기업과 5개 형성군을 독립 행으로 취급하지 않았습니다. ROE·규모·PBR는 특성 진단이며 완전한 인과 통제가 아닙니다.\n\n원문은 MSCI G와 배당 포함 수익률, 이 연구는 사외이사 비율과 가격수익률입니다. FF3/HAC/95% CI는 NOT_ESTIMATED, 독립 OOS는 UNVERIFIED입니다. 기존 FF3 원본과 사전 설계·실적은 보존했고 종목별 원천·API 키는 공개하지 않았습니다.\n\n[핵심 연구](CORE_HYPOTHESES.md) · [사건 감사](ECONOMIC_RETURN_RECOVERY.md) · [PDF](../reports/RESEARCH_REPORT.pdf)\n"
    (root/'docs/INTERVIEW_BRIEF.md').write_text(interview)
    def table_html(rows):
        return '<div class="scroll"><table>'+''.join('<tr>'+''.join(f'<{"th" if i==0 else "td"}>{html.escape(str(c))}</{"th" if i==0 else "td"}>' for c in row)+'</tr>' for i,row in enumerate(rows))+'</table></div>'
    body='<section id="summary"><h2>Executive Summary</h2>'+table_html(hypothesis_table(r))+'<p>H1은 관측 방향이 음수, H2는 양수지만 각각 6/4개월로 경제적 가설의 근거는 부족합니다. H3는 동일가중에서 부호가 바뀝니다. FF3 미추정·독립 OOS 미검증.</p></section>'
    for title,content in parts[1:6]:
        body+='<section><h2>'+html.escape(title)+'</h2>'
        paragraphs=[]
        for paragraph in content.split('\n\n'):
            if paragraph.startswith('|'):
                rows=[[c.strip() for c in row.strip().strip('|').split('|')] for row in paragraph.splitlines() if not re.match(r'^\|\s*---',row)]
                paragraphs.append(table_html(rows))
                continue
            formatted=html.escape(paragraph.replace('**',''))
            formatted=re.sub(r'\[([^]]+)\]\(([^)]+)\)',lambda m:'<a href="'+(m[2] if m[2].startswith('http') else REPO+'/blob/main/'+m[2])+'">'+m[1]+'</a>',formatted)
            paragraphs.append('<p>'+formatted+'</p>')
        body+=''.join(paragraphs)
        if title in figures:body+=f'<img src="core/{figures[title]}.svg" alt="{html.escape(title)}; actual common window" loading="lazy">'
        if title.startswith('H3'):body+='<img src="core/robustness.svg" alt="Same six-month weighting sign reversal">'
        body+='</section>'
    body+=f'<section><h2>Appendix / 보존한 원문 해설과 감사</h2><p><a href="appendix.html">기존 기술 감사 화면</a> · <a href="{REPO}/blob/main/docs/ECONOMIC_RETURN_RECOVERY.md">11개 사건 감사</a> · <a href="{REPO}/blob/main/docs/REPORT_TO_IMPLEMENTATION_MAP.md">원문 목차·COE·개혁·반도체 대응</a> · <a href="core/hypothesis_results.json">핵심 JSON</a> · <a href="core/cell_monthly_returns.csv">네 셀 월수익률</a> · <a href="core/formation_diagnostics.csv">형성 특성</a> · <a href="core/observed_good_bad_monthly.csv">관측 단면</a> · <a href="core/forward_loss_12m.csv">12개월 후속 손실</a></p></section>'
    style="body{font:16px/1.75 system-ui,sans-serif;background:#f4f6fa;color:#17263a;margin:0}main{max-width:1050px;margin:auto;padding:32px 20px}h1{font-size:clamp(28px,4vw,44px);line-height:1.25}section{background:white;padding:28px;margin:25px 0;border-radius:12px}img{width:100%;height:auto}table{border-collapse:collapse;width:100%;font-size:14px}td,th{border-bottom:1px solid #dbe3ed;text-align:left;padding:12px;vertical-align:top}.scroll{overflow:auto}a{color:#165fa3}.tag{color:#65778b}@media(max-width:600px){section{padding:16px}td,th{min-width:110px}}"
    status=json.loads((root/'outputs/final/completion_status.json').read_text())
    page='<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VFS | 세 가지 핵심 가설 실증</title><style>'+style+'</style></head><body><main><p class="tag">EXPLORATORY POST-BASELINE · 2026-10-11 · PRICE_RETURN_ONLY</p><h1>거버넌스를 더한 가치평가,<br>실제 데이터는 무엇을 보여주는가?</h1><p><a href="'+REPO+'">README</a> · <a href="RESEARCH_REPORT.pdf">연구 PDF</a> · <a href="EXECUTIVE_BRIEF.pdf">Executive Brief</a> · <a href="'+REPO+'/blob/main/docs/INTERVIEW_BRIEF.md">면접 요약</a></p>'+body+'<footer><p>기존 주 분석 기준 문구: '+html.escape(legacy.replace('**',''))+'</p><p>비공개 종목별 원천은 공개하지 않았습니다. 모든 그래프는 실제 집계이며 원문 참고 성과를 혼합하지 않았습니다.</p></footer>'
    page+='<script id="result-data" type="application/json">'+json.dumps(result_summary(),ensure_ascii=False)+'</script><script id="core-hypotheses-data" type="application/json">'+json.dumps(r,ensure_ascii=False)+'</script><script id="final-evidence-data" type="application/json">'+json.dumps(status,ensure_ascii=False)+'</script></main></body></html>\n'
    (root/'dashboard/index.html').write_text(page)
    target=root/'dashboard/core';target.mkdir(exist_ok=True)
    for p in (root/'outputs/core_hypotheses').glob('*'):
        if p.is_file() and p.suffix in ['.json','.csv']:shutil.copyfile(p,target/p.name)
    for p in (root/'outputs/core_hypotheses/figures').glob('*.svg'):shutil.copyfile(p,target/p.name)
    for p in (root/'reports').glob('*.pdf'):shutil.copyfile(p,root/'dashboard'/p.name)


def build_pdf(brief=False, root=ROOT):
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
    root=Path(root);r,_=inputs(root);parts=sections(root)
    font=next(p for p in ['/System/Library/Fonts/Supplemental/AppleGothic.ttf','/usr/share/fonts/truetype/nanum/NanumGothic.ttf'] if Path(p).exists())
    pdfmetrics.registerFont(TTFont('CoreKorean',font))
    styles=getSampleStyleSheet()
    for s in styles.byName.values():s.fontName='CoreKorean';s.wordWrap='CJK'
    styles['Normal'].fontSize=9;styles['Normal'].leading=14;styles['Normal'].spaceAfter=9
    styles['Heading1'].fontSize=19;styles['Heading1'].leading=25;styles['Heading1'].spaceAfter=15
    styles.add(ParagraphStyle('Cell',fontName='CoreKorean',fontSize=8,leading=12,wordWrap='CJK'))
    story=[]
    def para(t,style='Normal'):
        t=re.sub(r'\[([^]]+)\]\(([^)]+)\)',lambda m:f'<link href="{m[2] if m[2].startswith("http") else REPO+"/blob/main/"+m[2]}">{html.escape(m[1])}</link>',t)
        t=t.replace('**','').replace('—','-').replace('–','-')
        story.append(Paragraph(t,styles[style]))
    def table(rows,widths=None):
        def cell(c):
            t=html.escape(str(c))
            t=re.sub(r'\[([^]]+)\]\(([^)]+)\)',lambda m:f'<link href="{m[2] if m[2].startswith("http") else REPO+"/blob/main/"+m[2]}">{m[1]}</link>',t)
            return Paragraph(t,styles['Cell'])
        x=Table([[cell(c) for c in row] for row in rows],colWidths=widths or [460/len(rows[0])]*len(rows[0]),repeatRows=1,hAlign='LEFT')
        x.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e3edf9')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#d6deea')),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
        story.extend([x,Spacer(1,12)])
    def figure(name,height=215):
        p=root/'outputs/core_hypotheses/figures'/(name+'.png')
        from PIL import Image as PILImage
        with PILImage.open(p) as im:w,h=im.size
        story.append(Image(str(p),width=460,height=460*h/w));story.append(Spacer(1,10))
    para('VFS: 세 가지 투자 가설의 실증'+(' | Executive Brief' if brief else ''),'Heading1')
    para('2026-10-11 KST | 독립 개인 Quant/ESG 연구 | 탐색적 확장 | PRICE_RETURN_ONLY')
    table(hypothesis_table(r),[78,110,157,115])
    if brief:
        para('H1: 2021-07~12, Low-Good -14.3847%, Low-Bad -9.0482%. H2: 2022-07~10, High-Good +2.5935%, High-Bad -7.4670%. 각각 6/4개월이며 같은 시장기간의 효과 비교가 아니다. 단순 수익률 차이는 가치 함정 회피나 COE 정당화의 인과 증거가 아니다.')
        para('기존 VFS 자체 8개월 -17.30%. VFS·Value·KOSPI 공통 6개월 -11.14%/-13.72%/-10.50%. 동일가중 spread -0.4158%p의 부호 반전과 G-규모 상관 0.3945~0.4731이 순수 G 효과 해석을 제한한다. G-neutral은 별도 공통 2개월이다.')
        figure('robustness')
        story.append(PageBreak());para('표본과 검증의 경계','Heading1')
        c=r['cross_section'];para(f"원천 G 4,540건·재무 4,382건·증빙 9,186개를 재검증했다. 적격 PIT 결합 782기업·38,742 기업-월. 고정 연간 형성의 단면은 {c['observed_security_months']:,}/{c['expected_security_months']:,}개 관측 기업-월, {c['firms']}기업·58개월·5개 형성군이다. 반복 기업-월은 독립 N이 아니며 선택된 단면은 NAV가 아니다.")
        table(loss_summary(root),[68,67,75,65,65,120])
        para('12개월 후속 가격 손실 ≤-30%는 완전한 종목 경로만의 탐색 결과다. 결측·우측 검열·생존 선택이 남고 후속 수익성 악화는 NOT_TESTED다. 사외이사 비율은 MSCI G와 다르다.')
        para('FF3/HAC3·6/95% CI: NOT_ESTIMATED (H1 6개월, H2 4개월, H3 6개월 <24). 단면의 기업/형성군 이중 군집 모형도 5개 형성군 < 최소10으로 미추정이다. 통계적 비유의와 표본 부족을 구분한다. 독립 OOS는 UNVERIFIED다.')
        para('2016-2020 PIT 공백, 배당·상폐·기업행동·모집단·정정 이전 공시가 미검증이다. 기존 11개 사건의 16개 접수번호·37개 본문 절을 조사했으나 경제적 수익률 수정 0건. 가격경로 재현은 투자 가능성 검증과 다르다.')
        para(f'<link href="{REPO}">README 및 코드</link> | <link href="{PAGES}">실증 대시보드</link> | <link href="{REPO}/blob/main/docs/INTERVIEW_BRIEF.md">면접 요약</link>')
    else:
        para(parts[0][1].split('\n\n')[-2]);para(parts[0][1].split('\n\n')[-1])
        for index,(title,content) in enumerate(parts[1:],1):
            story.append(PageBreak());para(title,'Heading1')
            for position,paragraph in enumerate(content.split('\n\n')):
                if paragraph.startswith('|'):
                    rows=[[c.strip() for c in row.strip().strip('|').split('|')] for row in paragraph.splitlines() if not re.match(r'^\|\s*---',row)]
                    table(rows)
                else:para(paragraph)
                if index in [2,4] and position==0:figure('h1' if index==2 else 'h3')
            chart={1:'structure',2:'h1',3:'h2',4:'h3'}.get(index)
            if chart and index not in [2,4]:figure(chart)
            if index==5:figure('robustness')
    path=root/'reports'/('EXECUTIVE_BRIEF.pdf' if brief else 'RESEARCH_REPORT.pdf')
    doc=SimpleDocTemplate(str(path),pagesize=(595.28,841.89),leftMargin=66,rightMargin=66,topMargin=48,bottomMargin=48,title='VFS Three Hypotheses'+(' Executive Brief' if brief else ''),author='Independent personal research')
    def footer(c,d):
        c.setFont('CoreKorean',8);c.setFillColor(colors.HexColor('#68778b'));c.drawString(66,25,'VFS | EXPLORATORY | PRICE_RETURN_ONLY | LIMITED EVIDENCE');c.drawRightString(529,25,str(d.page))
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return path


def verify(root=ROOT):
    root=Path(root);r,cells=inputs(root)
    for key,good,bad in [('H1_low_pbr_governance',*CELLS[:2]),('H2_high_pbr_governance',*CELLS[2:])]:
        actual=paired_description(cells,good,bad)
        for field in ['months','start','end','mean_monthly_good_minus_bad_pp','good_cumulative_pct','bad_cumulative_pct','positive_spread_months','negative_spread_months']:
            if isinstance(actual[field],float):assert np.isclose(actual[field],r[key][field],atol=1e-12,rtol=0),field
            else:assert actual[field]==r[key][field],field
    inference=pd.read_csv(root/'outputs/core_hypotheses/cell_inference.csv')
    short=inference.n_months.lt(24)
    assert inference.loc[short,'status'].eq('NOT_ESTIMATED').all()
    assert inference.loc[short,['alpha','p_hac','ci_low','ci_high','p_holm']].isna().all().all()
    for rel,sha in json.loads((root/'docs/core_baseline_hashes.json').read_text())['files'].items():
        assert digest(root/rel)==sha,'baseline changed: '+rel
    page=(root/'dashboard/index.html').read_text()
    embedded=json.loads(re.search(r'<script id="core-hypotheses-data" type="application/json">(.*?)</script>',page,re.S)[1]);assert embedded==r
    for file in ['README.md','reports/RESEARCH_REPORT.md','reports/EXECUTIVE_BRIEF.md','docs/CORE_HYPOTHESES.md','docs/INTERVIEW_BRIEF.md','dashboard/index.html']:
        text=(root/file).read_text()
        if (root/'outputs/supplement/summary.json').exists():
            if file!='docs/CORE_HYPOTHESES.md':
                assert '거버넌스는 PBR에 추가적인 투자 정보를 제공하는가?' in text
        else:
            for h in ['H1','H2','H3']:assert h in text
        for key in ['H1_low_pbr_governance','H2_high_pbr_governance']:
            assert f"{r[key]['mean_monthly_good_minus_bad_pp']:+.4f}" in text,'numeric narrative mismatch '+file
    forbidden={'stock_code','code','name','rcept_no','source_hash','financial_source_hash'}
    for p in (root/'outputs/core_hypotheses').glob('*.csv'):
        assert not forbidden.intersection(pd.read_csv(p,nrows=0).columns),'security rows '+p.name
    for p in (root/'outputs/core_hypotheses').glob('*'):
        if p.is_file() and p.suffix in ['.csv','.json']:assert digest(p)==digest(root/'dashboard/core'/p.name),'stale dashboard aggregate'
    print('CORE_PUBLICATION_VERIFIED: real arithmetic, baseline hashes, inference gates, narrative, aggregates')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['charts','sync','pdf','verify']);a=parser.parse_args()
    if a.command=='pdf':build_pdf();build_pdf(brief=True)
    else:globals()[a.command]()


if __name__=='__main__':main()
