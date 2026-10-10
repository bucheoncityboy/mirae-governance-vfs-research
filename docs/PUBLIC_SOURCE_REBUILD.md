# GitHub 자료에서 이어가는 VFS 원천 재구축

2026-10-11 KST. 기준 VFS commit `c8abb0f`, FF3 commit `dc47a81`. 이전 PC 경로·비공개 parquet·응답 캐시를 사용하지 않고 두 공개 저장소를 새로 clone했다. 기존 설계와 결과는 [별도 스냅샷](../snapshots/public-c8abb0f/manifest.json)에 보존했다.

## 공개 결과와 원천 재실행의 구분

[공개 산술 검사](../outputs/reconstruction/published_arithmetic.json)는 이미 게시된 월별 수익률을 재검산한다. VFS 자체 8개월 -17.30%, 공통 6개월 VFS -11.14%·Value -13.72%·KOSPI -10.50%, 월평균 차이 +0.4325%p가 일치했다. 이 검사만으로 종목별 원천 자료에서 VFS를 다시 실행했다고 주장하지 않는다. FF3 알파는 `NOT_ESTIMATED`다.

[FF3 입력 목록](../outputs/reconstruction/ff3_input_inventory.json)은 GitHub에서 받은 여섯 parquet의 SHA256·크기·기간·스키마를 기록한다. [수익률 감사](../outputs/reconstruction/return_audit_summary.json)는 원가격과 원수익률을 실제로 대조했다. ±100% 필터 659건과 결측 1,716건을 확인했고, 유효 가격수익률의 산술 오차는 0이다. 기업행동·상폐 대가·배당을 공식 증빙으로 입증한 경제적 수익률 수정은 수행하지 않았다. 월별 결측 분류는 겹칠 수 있으며 단순 합계를 총 결측으로 사용하지 않는다.

공개 경로 진단에서 VFS와 Value는 각각 5개 월에 보유수익률 결측으로 연간 경로가 처음 중단됐다. 종목별 원인은 재구축한 실제 보유비중으로 별도 조사해야 하며 공개 CSV만으로 659건 중 편입종목을 특정할 수는 없다.

## 공식 공시 재수집

[OpenDART 공시검색](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019001), [사외이사](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS002&apiId=2020012), [단일회사 주요계정](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2019016)의 인증키·응답·접수번호·공시일을 직접 확인한다. 고유번호 ZIP 경로가 정상 ZIP을 반환하지 않아 기존 수집 코드의 과거 `list.json` 매핑을 사용했다. 현재 상장 집합을 과거로 소급하지 않는다.

[접근 검사](../outputs/reconstruction/api_access_probe.json)와 [소규모 수집 검증](../outputs/reconstruction/smoke_summary.json)은 포트폴리오 성과 검정과 별개다. 기존 고정 5종목·5연도 및 보조 분기 보고서를 사용해 18개 G 관측과 14개 재무 관측을 원응답 해시·접수번호·이사 수·공시일·KRW 장부자본과 대조했다. 실제 미제공 응답 `013`도 기록하며 결측을 대체하지 않는다. 과거 원정정 이전 값은 재수집만으로 확정할 수 없다.

[수집 예산](../outputs/reconstruction/acquisition_budget.json): 1,054종목 원패널에서 8,617개 연간 기업·연도 조합, 단일회사 G·재무 API 기준 17,234회에 매핑·재시도가 추가된다. 단일 실행 상한은 19,000회이며 실행 재개 때 이미 사용한 요청을 차감했다. [공식 안내](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS002&apiId=2020012)의 일반적인 제한은 계정 설정에 따라 다를 수 있으므로 `020` 응답에서는 수집을 중단한다.

어댑터는 `legacy_governance_pilot/src`의 함수에 새 `ROOT/SOURCE`를 실행 시 바인딩한다. 과거 파일·상대경로·설계 잠금을 수정하지 않는다. 캐시는 원응답 SHA256를 확인하고 재사용하며 새 수집 시각과 수정을 별도 버전으로 기록한다. 기존 SHA를 맞추는 과정은 없다.

## 새 환경 실행

아래 `WORK`는 새 환경에서 소유자가 정한 경로다. 기존 PC의 파일이 필요하지 않다.

```sh
WORK="$PWD/vfs-public-work"
mkdir -p "$WORK/private"
chmod 700 "$WORK/private"
git clone --branch codex/public-source-rebuild-20261011 https://github.com/bucheoncityboy/mirae-governance-vfs-research.git "$WORK/vfs"
git clone https://github.com/bucheoncityboy/fama-french-integrated-research.git "$WORK/ff3"
python3.12 -m venv "$WORK/.venv"
"$WORK/.venv/bin/python" -m pip install -r "$WORK/vfs/requirements.txt"
"$WORK/.venv/bin/python" -m pip install -e "$WORK/vfs" --no-deps
cd "$WORK/vfs"
export VFS_FF3_ROOT="$WORK/ff3/korea-market"
export VFS_LEGACY_ROOT="$WORK/private/recollected"
"$WORK/.venv/bin/python" -m pytest -q
"$WORK/.venv/bin/python" -m vfs_research.cli verify-public
"$WORK/.venv/bin/python" -m vfs_research.reconstruction public-audit \
  --ff3-root "$VFS_FF3_ROOT" --workspace "$WORK/private"
# 화면에 표시되지 않는 보안 입력. 키는 Git 밖에 권한 0600으로 저장한다.
"$WORK/.venv/bin/python" scripts/configure_dart_key.py --private-dir "$WORK/private"
"$WORK/.venv/bin/python" -m vfs_research.reconstruction smoke \
  --ff3-root "$VFS_FF3_ROOT" --workspace "$VFS_LEGACY_ROOT" \
  --key-file "$WORK/private/opendart-key" --budget 200
# PASS_PARTIAL_COVERAGE와 요청 예산을 확인한 뒤에만 전체 수집한다.
"$WORK/.venv/bin/python" -m vfs_research.reconstruction collect \
  --ff3-root "$VFS_FF3_ROOT" --workspace "$VFS_LEGACY_ROOT" \
  --key-file "$WORK/private/opendart-key" --budget 19000 --stage all
"$WORK/.venv/bin/python" -m vfs_research.reconstruction build \
  --ff3-root "$VFS_FF3_ROOT" --workspace "$VFS_LEGACY_ROOT"
"$WORK/.venv/bin/python" -m vfs_research.reconstruction_replay \
  --ff3-root "$VFS_FF3_ROOT" --workspace "$VFS_LEGACY_ROOT" \
  --output "$WORK/vfs/outputs/reconstruction"
```

수집 재개에는 같은 버전의 캐시를 사용한다. 백테스트 재실행 폴더가 이미 있으면 덮어쓰지 않고 새 버전을 만든다. `reconstruction_replay`는 기존 VFS 엔진을 별도 폴더에 복원해 `gate-a → data-build → backtest → factor-test → audit → figures`를 실행한다. 원문과 다른 대리지표, 가격수익률 기준, 결측 이후 연간 경로 중단, 조건부 FF3 팩터의 제약도 유지한다.

## 후속 탐색 분석과 공개 범위

[별도 후속 분석계획](../config/public_rebuild_followup_plan.yaml)은 새로운 전략 성과를 보기 전에 commit `8c34508`로 잠갔다. 기존 설계 해시는 그대로다. 추가 G-neutral 비교는 동일 PIT 모집단의 Low/High PBR 구간 예산을 50:50으로 맞추고 각 구간 전체 종목을 lagged-ME capped-VW로 보유한다. G에 따라 선별하지 않지만 연속 PBR 분포·규모까지 같아지는 것은 아니다. 새로운 주전략이나 인과 검증으로 해석하지 않는다. 충분한 공통 연속기간 없이 알파·HAC·신뢰구간을 산출하지 않는다. 독립 OOS는 계속 미검증이다.

FnGuide 일반 정책은 분석 용도와 무단 공유를 구분한다. 공개 GitHub 접근 가능 여부는 데이터 재배포 권한의 증거가 아니다. [공식 데이터 정책](https://help-dataguide.fnguide.com/ko/articles/%EC%9D%B4%EC%9A%A9-%EB%B0%8F-%EC%9A%94%EA%B8%88-%EC%95%88%EB%82%B4-48b18a4b)에 따라 이 작업은 소유자가 요청한 로컬 분석에 한정하고 원천·종목별 파생자료는 어느 GitHub 저장소에도 새로 게시하지 않는다. OpenDART도 [이용약관](https://opendart.fss.or.kr/intro/terms.do)의 이용·인증정보 조건을 따른다. 원응답, 키, 비공개 경로를 공개 검증 결과에 포함하지 않는다.

전체 수집·재구축·새 빈티지 결과와 기존 결과의 차이는 완료 후 별도 요약으로 연결한다. 이 문서만으로 원천 VFS 재실행 완료를 주장하지 않는다.
