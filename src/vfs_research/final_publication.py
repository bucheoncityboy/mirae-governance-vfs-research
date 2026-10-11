"""Synchronize the concluding narrative with public final evidence tables."""
import html
import json
from pathlib import Path
import re
import shutil

import pandas as pd

from .data_ingest import ROOT


def sync():
    final=ROOT/'outputs/final'
    status=json.loads((final/'completion_status.json').read_text())
    proof=json.loads((final/'raw_replay_validation.json').read_text())
    returns=pd.read_csv(final/'baseline_vs_final.csv')
    if status['classification']!='COMPLETE_LIMITED_EVIDENCE' or not returns.baseline_n.eq(returns.final_n).all():
        raise ValueError('publication requires the stated limited-evidence conclusion')
    readme=ROOT/'README.md';text=readme.read_text()
    block=f'''<!-- FINAL_EVIDENCE_START -->
### 결측은 어떤 경제적 사건이었는가?

원문 p21·p28의 장기 성과와 비교하려면 종목의 가격뿐 아니라 현금·신주·거래 가능성까지 이어져야 합니다. VFS 7건과 Value 6건의 첫 보유 결측을 중복 제거한 **11개 사건**을 조사했습니다. 후보 58개에서 관련 **{status['official_documents']}개 접수번호·{status['official_sections']}개 공식 본문 절**을 확인했습니다. 일부 교환 대가와 일정은 확인했지만 실제 지급·월말 평가·수정주가 기준을 함께 입증하지 못해 **수익률 수정은 0건**입니다. [사건별 근거와 판정](docs/ECONOMIC_RETURN_RECOVERY.md).

2021년 12월의 현금·신주 권리 전환은 공통기간 마지막 달의 경제적 평가에도 영향을 줄 수 있습니다. 2022/2024년에는 6월 말 형성 이전 거래정지 사례도 확인했습니다. 따라서 기존 8/6개월 수치는 동일 정의의 **가격 데이터 경로**를 재현한 결과이며 투자 가능한 총수익률은 아닙니다. 이번 오프라인 재실행에서도 월수익률 차이 1e-12 초과는 0건입니다.

![관측된 최초 중단 노출: 2022-01~2025-09, 10개 전략 중단월·13개 보유 기록·11개 고유 사건; 가격경로 gross 0bp, 원문 수치 아님](outputs/final/figures/held_gap_exposure.svg)

미확인 비중에 -100/-50/+50/+100% 수익률을 가정한 기여분을 별도 표시했습니다. **실측 성과·신뢰구간·가능 범위의 상하한이 아니며 NAV를 연장하지 않습니다.** 작은 비중도 결측을 0으로 채울 근거가 되지 않습니다.

![가정 기반 미확인 포지션 기여분: 같은 10개 중단월, 실측 비중 × 가정 수익률; 배당·비용 반영 포트폴리오 성과 아님, 기간 연장 없음](outputs/final/figures/missing_scenarios.svg)
<!-- FINAL_EVIDENCE_END -->

'''
    text=re.sub(r'<!-- FINAL_EVIDENCE_START -->.*?<!-- FINAL_EVIDENCE_END -->\s*','',text,flags=re.S)
    text=text.replace('## 07. What Held Up, What Did Not',block+'## 07. What Held Up, What Did Not')
    old='**VFS 백테스트 상태: 부분 관측 / EMPIRICAL_LIMITED.**'
    text=text.replace(old,'**한정 연구 완료: COMPLETE_LIMITED_EVIDENCE · VFS 실증 범위: EMPIRICAL_LIMITED.**')
    conclusion='연구 결과물은 원천 재현·11건 사건 감사·미추정 판정을 갖춘 한정 연구로 완결했습니다. [가설별 결론](docs/RESEARCH_CONCLUSION.md), [면접 요약](docs/INTERVIEW_BRIEF.md), [기준 대비 최종 비교](outputs/final/baseline_vs_final.csv)를 함께 제공합니다. 장기 투자전략·FF3 알파·독립 OOS의 검증 완료를 뜻하지 않습니다.\n\n'
    if '[가설별 결론]' not in text:text=text.replace('## Appendix A. Scope of Replication',conclusion+'## Appendix A. Scope of Replication')
    figure=re.search(r'!\[VFS 자체의 실제 연속 보유경로[^\n]+\n',text)
    if figure:
        chart=figure.group();text=text.replace(chart,'');text=text.replace('읽는 순서:',chart+'\n읽는 순서:',1)
    text=text.replace('원본 정리와 포트폴리오 갱신은 안전한 PR로 진행하며 사용자 승인 없이 병합하지 않습니다.',
                      '원본 FF3와 과거 결과는 보존했습니다. 공개 변경은 PR 검사와 배포 검증을 거칩니다.')
    readme.write_text(text)
    text=text.replace('공식 공시 제목에서 기업행동 후보 58개를 찾았어도 지급 대가·조정 조건은 미검증이므로 수익률 수정은 0건입니다.',
        '이전 제목 후보는 58개입니다. 후속 본문에서 일부 계약상 교환 조건을 확인했지만 양월 경제적 평가·실제 지급은 미검증이어서 수정은 0건입니다.')
    text=text.replace('문서·대시보드 변경은 PR 승인을 거쳐 병합·배포해야 합니다.',
        '공개 변경은 PR 필수 검사와 배포 검증을 거칩니다. [최종 검증](outputs/final/raw_replay_validation.json).')
    text=re.sub(r'\n{3,}','\n\n',text)
    readme.write_text(text)
    # Preserve Markdown prose; only relative link targets change for reports/.
    report=re.sub(r'\]\(([^)]+)\)',lambda m: ']('+(
        m[1] if m[1].startswith(('http:','https:','#')) else m[1][8:] if m[1].startswith('reports/') else '../'+m[1])+')',text)
    (ROOT/'reports/RESEARCH_REPORT.md').write_text(report)
    brief=ROOT/'reports/EXECUTIVE_BRIEF.md';b=brief.read_text()
    b=re.sub(r'<!-- FINAL_BRIEF_START -->.*?<!-- FINAL_BRIEF_END -->\s*','',b,flags=re.S)
    b=b.rstrip()+f'''\n\n<!-- FINAL_BRIEF_START -->
한정 연구 완료 **COMPLETE_LIMITED_EVIDENCE**. 공식 본문 {status['official_documents']}개 접수번호·{status['official_sections']}개 절로 보유 결측 11건을 조사했습니다. 실제 지급·월말 수량·가격을 함께 검증하지 못해 경제적 수익률 수정은 0건이며, 새로운 연속기간은 8/6개월 그대로입니다. G-neutral은 공통 2개월이고 알파·HAC·CI는 미추정입니다.

2021년 12월 권리 전환과 2022/2024년 형성 전 거래정지 때문에 기존 가격 경로를 투자 가능한 NAV로 해석할 수 없습니다. 독립 OOS·생존·상폐·배당 제약은 남아 있습니다. [사건별 감사](../docs/ECONOMIC_RETURN_RECOVERY.md) · [최종 결론](../docs/RESEARCH_CONCLUSION.md) · [면접 요약](../docs/INTERVIEW_BRIEF.md).
<!-- FINAL_BRIEF_END -->
'''
    brief.write_text(b)
    dashboard=ROOT/'dashboard/index.html';page=dashboard.read_text()
    page=page.replace('VFS 백테스트 · 부분 관측 / EMPIRICAL_LIMITED','한정 연구 완료 / COMPLETE_LIMITED_EVIDENCE · 실증 범위 EMPIRICAL_LIMITED')
    page=re.sub(r'<section id="economic-evidence">.*?</section>','',page,flags=re.S)
    section=f'''<section id="economic-evidence"><h2>경제적 수익률 감사와 한정 연구 결론</h2><p>COMPLETE_LIMITED_EVIDENCE · 실증 범위 EMPIRICAL_LIMITED. 11개 고유 사건의 공식 접수번호 {status['official_documents']}개, 본문 {status['official_sections']}개 절을 확인했습니다. 일부 교환 조건은 확인됐지만 월말 평가·실제 지급·조정 가격 기준이 부족해 수정은 0건입니다.</p><p>기존 8/6개월 가격 경로는 이번 원천 재실행에도 그대로입니다. 12월 권리 전환과 형성 이전 거래정지는 투자 가능한 NAV가 미검증임을 보여줍니다. FF3/HAC/CI 미추정, G-neutral N=2, 독립 OOS 미검증.</p><img src="final/held_gap_exposure.svg" alt="관측된 첫 중단 미확인 노출. 2022-01~2025-09, 10전략 중단월, 13보유 기록, 가격경로 gross 0bp"><p>관측된 미확인 노출: 10개 전략 중단월·13개 보유 기록·11개 고유 사건. 원문 성과 인용 없음.</p><div style="background:#fff5e6;padding:16px;border-radius:12px"><h3>별도 가정 분석: 실측 수익률 아님</h3><img src="final/missing_scenarios.svg" alt="가정만의 미확인 포지션 기여분. 실측 성과, 신뢰구간 또는 상하한이 아님"><p>같은 중단월의 실제 비중 × -100/-50/+50/+100% 가정. 완전한 포트폴리오 수익률과 배당·비용 성과가 아니며 NAV를 연장하지 않습니다. 100% 초과 상승도 가능합니다.</p></div><p><a href="https://github.com/bucheoncityboy/mirae-governance-vfs-research/blob/main/docs/ECONOMIC_RETURN_RECOVERY.md">사건별 공식 근거</a> · <a href="https://github.com/bucheoncityboy/mirae-governance-vfs-research/blob/main/docs/INTERVIEW_BRIEF.md">면접 요약</a> · <a href="https://github.com/bucheoncityboy/mirae-governance-vfs-research/blob/main/outputs/final/baseline_vs_final.csv">기준 대비 최종 비교</a></p></section>'''
    page=page.replace('<footer>',section+'<footer>',1)
    page=page.replace('기업행동 후보 공시 58개를 찾았지만 지급 대가와 조정 조건은 미검증입니다.',
        '앞선 후보 58개는 제목 탐색입니다. 후속 본문 감사에서 일부 계약상 조건을 확인했으며 월말 경제적 평가는 여전히 미검증입니다.')
    page=re.sub(r'<script id="final-evidence-data".*?</script>','',page,flags=re.S)
    page=page.replace('</main>', '<script id="final-evidence-data" type="application/json">'+json.dumps(status,ensure_ascii=False)+'</script></main>')
    dashboard.write_text(page)
    target=ROOT/'dashboard/final';target.mkdir(exist_ok=True)
    for p in (final/'figures').glob('*.svg'):shutil.copyfile(p,target/p.name)
    for p in final.glob('*.csv'):shutil.copyfile(p,target/p.name)
    shutil.copyfile(final/'completion_status.json',target/'completion_status.json')


if __name__=='__main__':
    sync();print('FINAL_NARRATIVE_SYNCHRONIZED_WITH_AGGREGATE_EVIDENCE')
