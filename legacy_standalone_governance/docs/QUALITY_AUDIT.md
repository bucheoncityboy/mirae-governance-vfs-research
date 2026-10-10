# 품질 감사 — 2026-10-09

| 항목 | 판정 | 근거와 범위 |
| --- | --- | --- |
| 기존 FF3 수익률 수치 재현 | PASS | 311개월·원본 스크립트 별도 실행 대조, 최대 절대오차 1.11×10⁻¹⁶ |
| 원본 보존 | PASS | 원본 120개 파일 전후 SHA-256 동일 |
| 새 연구/출처 숫자 구분 | PASS | 기존 FF3 재현값과 참고 리서치 숫자, G 미추정 상태를 구분 |
| 정보 시점·정정공시 로직 | PASS(합성 테스트) | 과거 기간 정정, 월말 공시, 미래정보 차단; 실제 G 패널은 미확보 |
| 원응답 해시·숫자 대조 | PASS(합성 테스트) | 실제 파일 없이 해시 문자열만 있는 관측은 제외 |
| 포트폴리오 가중·누락 수익률 | PASS(합성 테스트) | 구성종목 기준 가중합, 누락 종목의 사후 재가중 금지 |
| RF 처리·회귀 | PASS(합성 테스트) | 자기금융 스프레드/롱온리, 알려진 알파·베타, 공통 연속 월·HAC 순서 |
| 자격정보 보안 | PASS(합성 테스트) | 오류와 manifest에 키/키 포함 URL을 기록하지 않음 |
| 실제 G 공시값/공개일 | NOT_TESTED | 역사적 자료·인증키 미확보, G 알파를 계산하지 않음 |
| 원본 6월 BE 회계연도 | FAIL(원본 규약) | t-1이라는 문서 설명과 달리 t-2 값. 독립 spec_aligned 비교를 제공 |
| 원본 6월 BM 사용 | FAIL(원본 규약) | 6월 panel.bm은 직전 구성연도; 현재 6월 ME 기준과 달라짐 |
| 배당·상폐·상장시장 구분 | NOT_TESTED | 메타데이터와 원 유니버스 추가 확인 필요 |
| 업종·수익성·거래비용 통제 | NOT_TESTED | 검증 가능한 입력이 없어 미추정 |
| 새 G 알파·COE·인과 결론 | NOT_TESTED | 추정/입증됐다고 주장하지 않음 |

## 실행 검증

`python -m pytest -q tests`: **33 passed**.

`python -m src.pipeline --source <pinned original checkout>`: **limited / fallback_c, ff3_reproduced=True**.

원본 construct_6_portfolios.py를 별도 폴더에서 원본 parquet에 읽기 전용으로 연결해 실행했다. 생성된 월별 MKT−RF/SMB/HML/RF를 새 legacy_compatible CSV와 대조했다. 결과는 [original_script_comparison.csv](../korea-market/governance-extension/output/original_script_comparison.csv)에 보관했다.

원본 문제를 고친 것처럼 기존 연구를 덮어쓰지 않았다. 원본 재현과 별도 규약의 민감도를 함께 공개한다. 원본 GRS·25개 포트폴리오 전체 모델 재현은 이번 검증 범위에 포함하지 않는다.
