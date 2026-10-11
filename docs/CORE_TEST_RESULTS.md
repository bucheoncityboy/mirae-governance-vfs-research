# 핵심 가설 확장 검증

2026-10-11 KST. Python 3.12.14. 로컬 `pytest -q`: **68 passed**. `compileall -q src`, `git diff --check`, `vfs_research.cli verify-public`, `core_publication verify` 통과.

검사에는 미래 공시·중복 관측 거부, 종목 결측 이후 다음 형성까지 셀별 중단, 끊긴 월 연결 금지, RF 차감·24개월 추론 조건·16개 사양 Holm, 월별 재선정 금지, 12개월 손실 결측/우측 검열 분리, 5개 형성군의 군집 추론 금지, 실제 공개 셀 수익률 산술·표본·문서·Pages 집계 일치와 기존 290파일 해시 보존이 포함된다.

실제 원천 G·BE·접수번호·공시일·원응답 해시를 확인하고 네 셀 실증을 실행했다. 기존 124개월 VFS·Value·KOSPI 월수익률은 결측 위치 포함 1e-12 초과 변경 0건이다. 주 분석계획·backtest.py·portfolio.py와 이전 스냅샷은 바이트 그대로다. 종목별 자료나 API 키를 공개하지 않았다.

연구보고서 8쪽·Executive Brief 2쪽을 Poppler로 렌더링해 전 페이지를 검사했다. 표·그림·각주 겹침을 수정한 최종본에 대한 검증이다. 로컬 Pages 화면에서 가설 표와 실측 그림을 확인했으며 모든 최신 본문 상대 링크는 공개 검증을 통과한다.

원격 CI와 배포는 로컬 검사와 구분한다. 실제 원격 상태는 [PR #5 검사](https://github.com/bucheoncityboy/mirae-governance-vfs-research/pull/5/checks), [Actions](https://github.com/bucheoncityboy/mirae-governance-vfs-research/actions), [Pages](https://bucheoncityboy.github.io/mirae-governance-vfs-research/)에서 확인한다. 완료 보고에는 실제 확인한 원격 실행과 병합·배포 상태만 기재한다.
