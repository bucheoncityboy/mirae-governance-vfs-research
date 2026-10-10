# 데이터 사전과 실행 조건

## 공시 G 관측 (`governance_observations.csv`)

| 필드 | 정의 |
| --- | --- |
| stock_code | 6자리 문자열. 원본에는 0120G0·0126Z0이 있어 영문을 보존한다 |
| corp_code | DART 8자리 문자열 |
| rcept_no | 실제 응답과 목록에서 대조한 14자리 공시접수번호 |
| report_title | 실제 목록의 보고서명; 정정 여부 보존 |
| filing_date | `list.json`의 rcept_dt. 기준연도 말·번호 접두어로 대체 금지 |
| period_end | 원응답 stlm_dt의 경제적 측정일 |
| available_at | filing_date 다음 날부터 도달하는 첫 월말 또는 더 늦은 시점 |
| outside_directors / total_directors | 비음수 정수 수; 전체 >0, 사외≤전체 |
| g_value | outside_directors/total_directors; 0~1 |
| unit | ratio_0_1 |
| source_field / raw_value | 원필드와 원값; 숫자 추정/빈값 0 대체 금지 |
| source_url | 접수번호와 일치하는 공식 DART 뷰어 |
| source_hash / filing_list_hash | 캐시된 공식 원응답과 공시목록 응답의 SHA-256 |
| collected_at | 수집 UTC 시각 |
| qa_status / missing_reason | PASS 또는 EXCLUDED; 실패 사유 |
| is_amendment | 공시명에 정정 표시가 있는지 |

`raw/`와 개인 코드 매핑·인증키는 버전 관리에서 제외한다. `manifest.csv`는 인증키를 제외한 쿼리와 해시를 저장한다. 이전 수집 스냅샷을 삭제하거나 현재 응답을 과거 원본인 것처럼 쓰지 않는다. API 요약이 최신 정정 공시만 반환해 과거 원본을 얻지 못하면 그 원본의 역사적 관측은 누락으로 처리한다.

## 재무 공개일 근거 (`financial_filings.csv`)

필수: `stock_code,formation_year,be_year,financial_filing_date,rcept_no,source_url`. `be_year=formation_year-1`이고 실제 공개일은 해당 연도 6월 30일보다 앞서야 한다. 공식 공시와 원본 장부자본 값의 대응을 사용자가 원자료로 검수한 증빙이어야 한다. CSV의 날짜·링크만으로 그 검수를 자동 완료했다고 주장할 수 없다.

## 기존 시장 데이터

`return`: 소수 월수익률. `me`: 천원. `be`: 억원. `bm`: BE / (ME/100000). 매월 시가총액 가중은 직전 달 관측만 허용한다. 날짜가 월초인 것은 해당 수익률 월의 라벨이며 월초부터 지표를 관찰했다는 뜻이 아니다.

기존 6월 BE 시점과 시장구분 플래그는 감사 결과를 확인한다. 배당 포함, 상폐 수익률, 원 유니버스 PIT와 업종정보는 미확인 상태다.

## 결과

- `ff3_factors_*.csv`: 기초 팩터 재구성; G 성과가 아님.
- `data_coverage.csv`: 현재 fallback에는 연도별 원본 표본과 G 미결합 상태. 실증 경로에는 월별 joint coverage.
- `sort_returns.csv`, `factor_alpha.csv`, `robustness.csv`: 충분한 검증 입력이 없으면 빈 수익률 표/NA/미추정 사유.
- `RESULT_STATUS.json`: 상태·완료 범위·필요 자료. `limited`를 완료된 G 연구로 표현하지 않는다.
