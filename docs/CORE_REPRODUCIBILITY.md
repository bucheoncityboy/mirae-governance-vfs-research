# 핵심 가설 실증 재현

Python 3.12, 저장소 requirements.txt와 editable 설치를 사용한다. 원천 종목 자료는 이 저장소에 포함하지 않는다. 공개 집계의 산술 검증과 원천 재실행은 다른 작업이다.

## 공개 검사

```sh
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
python -m pytest -q
python -m compileall -q src
python -m vfs_research.cli verify-public
python -m vfs_research.core_publication verify
```

CI는 기존 성과 산술·설계·스냅샷·원문 보존 검사와 새 가설 산술·군집/연속기간 조건·보안 열 검사·생성 문서 일치를 함께 실행한다. 공개 결과만으로 종목별 원천 재현까지 검증했다고 주장하지 않는다.

## 소유자 로컬 원천 실행

소유자에게 허용된 재구축 보관본 또는 기존 입력을 읽기 전용으로 지정한다. 원천을 공개 저장소로 복사하지 않는다. 설정 경로는 공개 문서에 남기지 않는다.

```sh
export VFS_LEGACY_ROOT=/authorized/local/recollected
export VFS_FF3_ROOT=/authorized/local/ff3/korea-market
python -m vfs_research.core_hypotheses --verified-local --out outputs/core_hypotheses
python -m vfs_research.core_publication charts
python -m vfs_research.core_publication pdf
python -m vfs_research.core_publication sync
python -m vfs_research.cli verify-public
```

`--verified-local`은 기존 `load_panel(verify=True)`로 원응답 해시와 G·BE·접수번호·공시일·PIT를 검증한 후 집계만 쓴다. 종목별 입력은 메모리에서만 사용한다. 원천 재수집이나 API 키가 필요 없다. 기존 `--private-panel`은 PIT 검증된 외부 파일에 대한 제한 JSON을 저장소 밖에만 쓰며 원천을 재해시했다고 주장하지 않는다. 두 입력 옵션을 동시에 쓰면 거부한다.

## 출력과 검증 단위

| 출력 | 의미 |
| --- | --- |
| cell_monthly_returns.csv | 네 셀의 연간 보유·드리프트, 월별 상태·최초 결측 수·비중 |
| cell_continuous_segments.csv | 각 셀과 H1/H2의 모든 유효 연속 블록 |
| formation_diagnostics.csv | PBR·시총·ROE·레버리지 분포, 가용 수·비중, HHI·유효 종목수 |
| cell_inference.csv | 16개 FF3/평균 spread HAC3/6 사양, 최소기간·Holm 조건 |
| observed_security_monthly.csv | 고정 형성 구성원 기대 N·관측 N·결측·관측 수익률·월 -20% 손실률 |
| observed_good_bad_monthly.csv | 같은 월·PBR군 Good/Bad 관측 평균과 결측률 |
| observed_by_size_stratum.csv / observed_by_roe_stratum.csv | 같은 형성 시점 PBR군 내 규모 3분위 / ROE 부호별 탐색 |
| observed_by_formation_year.csv | 5개 형성군별 기술통계; 독립 기업-월 검정 아님 |
| forward_loss_12m.csv | 12개월 ≤-30% 가격손실, 완전 경로·결측·우측 검열 |
| cross_section_inference.csv | 기업/형성군 이중 군집 사양 및 5<10 형성군 미추정 |
| hypothesis_results.json / hypothesis_judgments.csv | 실제 결과·표본·판정·원천 SHA·주 결과 불변성 |

7월 형성군 구성원은 다음 6월까지 고정한다. 월별 G를 보고 새로 분류하지 않는다. 관측 단면은 NAV가 끊긴 뒤에도 실제 관측 수익률을 요약할 수 있지만 결측 없는 종목의 선택편향을 그대로 가진다. 형성군 내 규모 순위는 PBR군별 시총 1/3·2/3 분위수이며 동점은 낮은 층에 둔다. 기대 기업-월 38,254와 PIT 결합 38,742는 다른 표본이다. 전자는 연간 형성 구성원의 보유기간 격자이고 후자는 월별 결합 적격 패널 전체다.

12개월 손실의 관측 단위는 기업·형성연도이며 같은 기업이 반복될 수 있다. 전체 평균을 독립 N의 p값으로 검정하지 않는다. 단면 모형은 월 고정효과, Good, log(ME), 연속 PBR, PIT ROE를 사용하고 기업·형성군으로 이중 군집한다. 10개 이상 형성군·30개 이상 기업·24개 이상 달을 확보할 때만 탐색적으로 추정한다. FF3의 24개월 전략 NAV 조건을 대체하지 않는다.

## 원천과 보존

이번 joint SHA는 기존 재구축 영수증과 같다. 기존 VFS·Value·Market의 모든 124개월 월수익률(결측 포함)은 1e-12 초과 차이 0건이다. 기존 집계·설계·legacy·스냅샷 290개 파일의 해시도 그대로다. 이전 보고서의 일부 상대 링크는 당시 위치 기준의 역사적 기록으로 보존했고, 최신 부록 링크는 README와 Appendix 화면을 사용한다.

PDF에는 한국어 TTF가 필요하다. macOS AppleGothic 또는 Linux NanumGothic을 사용한다. 그래프는 실측 집계만으로 그리며 날짜 메타데이터를 제거한 SVG를 게시한다. PDF는 렌더링 후 전 페이지의 표·줄바꿈·그림·각주를 검사한다.

[탐색 이력](CORE_DECISIONS.md) · [입력 영수증](../outputs/reconstruction/recollected_input_manifest.json) · [기존 재현](REPRODUCIBILITY.md)
