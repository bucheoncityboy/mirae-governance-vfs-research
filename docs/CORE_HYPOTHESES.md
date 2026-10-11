# 세 가지 핵심 가설로 보는 VFS 실증

> 미래에셋 「멀티플 탈출」 p20~23, p28의 핵심 전략 가설만 전면에 배치한 **독립 탐색 연구**입니다. 원문 8개 장을 다시 요약한 문서가 아닙니다. [원문 목차별 검증 이력](REPORT_TO_IMPLEMENTATION_MAP.md)은 증빙 부록으로 유지합니다.

## Research Question

**기업의 가치평가(PBR)에 거버넌스 정보를 더하면 가치 함정을 피하고, 높은 멀티플을 정당화할 기업을 선별하며, 그 결과 투자 가능한 포트폴리오가 개선되는가?**

| 가설 | 정확한 비교군 | 지금의 판정 | 주의 |
| --- | --- | --- | --- |
| **H1: Value trap** | 동일 Low-PBR 집단의 **Good G − Bad G** | **NOT TESTED** (공개 셀 수익률 없음) | 단순 VFS−Value는 H1 아님 |
| **H2: Justified premium** | 동일 High-PBR 집단의 **Good G − Bad G** | **NOT TESTED** (공개 셀 수익률 없음) | 프리미엄의 COE 인과효과와 다름 |
| **H3: Portfolio payoff** | VFS vs Value, KOSPI, PBR 50:50 G-neutral | **SHORT-WINDOW DESCRIPTIVE ONLY** | 스타일·규모·비중 차이가 남음 |

**H1/H2는 분석 미완료를 증거 없음이나 효과 없음으로 바꾸지 않습니다.** 공개된 `cell_formation_coverage.csv`에는 형성 기업 수만 있고, 셀별 실현 수익률은 없습니다. 기존 소유자용 PIT 원천 파일로 아래 모듈을 실행해야 수치 검정의 첫 단계를 끝낼 수 있습니다.

## H1 / H2 — 실제 구현된 비교방법

새 `src/vfs_research/core_hypotheses.py`는 **기존 적격기업 규칙과 연간 7월 형성, PBR 중앙값, PBR 집단별 G 중앙값, 형성 시 25% 셀 상한**을 그대로 재사용하여 Low-Good, Low-Bad, High-Good, High-Bad 네 셀의 월별 포트폴리오 수익률을 추적합니다.

각 셀은 형성 후 buy-and-hold drift를 적용합니다. **편입종목 하나라도 해당 월 수익률을 확인할 수 없으면 그 셀의 연간 경로를 다음 형성까지 중단**합니다. Good와 Bad의 *같은 연속 관측월*만 비교합니다. 단절된 월을 이어 붙이거나 결측을 0으로 대체하지 않습니다.

- H1: `R(Low-Good) - R(Low-Bad)`
- H2: `R(High-Good) - R(High-Bad)`

관측 시점이 다르거나 대조군의 결측이 많을 수 있어 H1/H2의 유효 기간은 독립적으로 보고합니다. 별도 신규 탐색이므로 원래 사전등록된 VFS 전략과 혼동하지 않습니다. 동등 PBR 집단이라도 집단 내 *연속 PBR·기업규모·산업·ROE*가 일치하지 않으므로 인과 검정은 아닙니다.

실제 승인된 `pit_panel.parquet`를 가진 소유자는 **공개 저장소 밖의 경로**로만 결과를 출력합니다.

```sh
python -m vfs_research.core_hypotheses --private-panel /authorized/local/pit_panel.parquet --out /authorized/local/core_claims_result.json
```

비공개 원천에 접근할 수 없다면 공개 자료 기반 H3만 재계산합니다.

```sh
python -m vfs_research.core_hypotheses
```

## H3 — 공개 원천에서 이미 확인된 범위

- VFS 자체 관측: **2021-07~2022-02, 8개월**, 누적 **-17.30%**. 동일 기간 KOSPI **-18.96%**.
- 같은 공통기간: **2021-07~2021-12, 6개월**, VFS **-11.14%**, Value **-13.72%**, KOSPI **-10.50%**.
- VFS−Value 평균: **월 +0.4325%p**. 기술통계일 뿐, 알파·유의성 입증 아님.
- 같은 6개월 EW 비교에서 차이는 **월 -0.4158%p**로 부호가 역전됨.
- PBR 50:50 G-neutral 비교: **연속 2개월**. FF3 알파·신뢰구간 추정 불가.
- G와 기업규모(log ME)의 상관: **0.3945~0.4731**(형성연도별). H3 차이를 순수 G 효과라 할 수 없음.

**판정:** 비교군 구성과 제한된 6개월 가격경로는 재현됐으나, 전략의 장기 투자 가능성·개별 G 기여·위험조정 초과수익의 실증은 미완료입니다. FF3 α, p, CI는 24개월 연속 공통 표본을 확보하지 못해 **NOT_ESTIMATED**입니다.

## 자료 한계와 실패 조건

원문 MSCI G가 아니라 **사외이사/전체 이사 비율**을 사용합니다. 원문 2016~2026년의 배당 포함 성과와 본 연구 PRICE_RETURN_ONLY gross 0bp 결과는 동일하지 않습니다. 현금·신주 권리, 거래 가능성, 배당·상폐 대가, 과거 생존집합, 과거 공시 정정 전 정보, 독립 OOS가 미검증입니다.

기존 소유자 원천 재실행에서 동일 월별 가격수익률 차이 1e-12 초과는 0건이지만 이 사실은 *투자 가능한 경제적 NAV*의 검증이 아닙니다. [11개 사건과 0건 복원 판정](ECONOMIC_RETURN_RECOVERY.md) · [기존 잠금 및 탐색 이력](DECISIONS.md).

**코드 구현은 가설별 비교를 가능하게 만드는 작업이고, 원천 접근 없이 가설을 실증했다고 선언하는 작업은 아닙니다.**
