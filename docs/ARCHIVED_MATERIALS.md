# 현재 VFS 연구와 과거 보존 자료의 구분

이 문서는 **현재 포트폴리오 리서치**와 **이전 프로젝트의 보존 기록**을 구분한다. 과거 파일은 출처와 변경 이력을 검증하기 위해 기존 경로에 유지했으며, 현재 투자성과를 추가로 입증하거나 새 결과와 합산하는 데 사용하지 않는다.

## 현재 연구에 해당하는 자료

- [README](../README.md): 현재 질문·핵심 실증·결론 및 한계
- [핵심 실증](../outputs/core_hypotheses/hypothesis_results.json): 저PBR·고PBR Good−Bad, VFS−Value의 원래 비교 결과
- [보완 실증](../outputs/supplement/summary.json): 동일 58개월의 특성 매칭과 배당 포함 부분 표본 민감도
- [방법과 재현](SUPPLEMENT_REPRODUCIBILITY.md): 공개 원천 범위, PIT·매칭·결측 처리 및 검증 방법
- [실증 대시보드](../dashboard/index.html): 현재 연구의 웹 표현

`outputs/core_hypotheses/`는 현재 결과의 **기존 기준 실증**으로, 다른 프로젝트의 결과가 아니다. `outputs/supplement/`는 이에 더한 탐색적 보완 분석이다.

## 과거 프로젝트·이력 보존용 (현재 분석 결과와 별개)

| 경로 | 용도 |
| --- | --- |
| [`legacy_governance_pilot/`](../legacy_governance_pilot/) | 초기 거버넌스·FF3 탐색 프로젝트를 원본 형태로 이관한 자료 |
| [`legacy_standalone_governance/`](../legacy_standalone_governance/) | 폐기된 독립 초기 연구 저장소의 보존 사본 |
| [`snapshots/`](../snapshots/) | 과거 단계별 파일·발간물의 기록 |
| [`MIGRATION_STATUS.md`](../MIGRATION_STATUS.md), [`docs/LEGACY_HISTORY.md`](LEGACY_HISTORY.md) | 저장소 분리·이관·과거 검증 이력 |
| `reports/*.pdf`, `dashboard/*.pdf` | 과거 발간물 보존본. 현재 README 및 Pages의 최종 결론과 구분 |

`dashboard/core-archive.html` 및 `dashboard/appendix.html`도 이전 분석 단계를 확인하기 위한 보존 화면이다. 실제 채용 제출용 안내는 상단의 **현재 연구** 항목을 기준으로 한다.

보존 파일은 원본 SHA와 이관 경로를 유지하기 위해 이동하거나 삭제하지 않았다. 과거 FF3 추정·초기 가설 결과는 현재의 사외이사 비율 기반 VFS 선별력 판단에 합산하지 않는다.
