# Reproducibility

Python 3.12. Install `python -m pip install -r requirements.txt` and `python -m pip install -e .`.
Public validation needs neither API credentials nor FnGuide source data:

```sh
python -m pytest -q
python -m compileall -q src
python -m vfs_research.cli verify-public
```

Real-data rerun requires authorized local inputs. Set `VFS_LEGACY_ROOT` to the original governance extension with private verified parquet and hashed DART response cache, and `VFS_FF3_ROOT` to the original `korea-market` local folder. The source panel hashes are recorded in `outputs/input_snapshot.json`; raw responses and individual security data are never in this repository.

Run in order: `gate-a`, `design-lock`, `data-build`, `backtest`, then supplementary `factor-test`, `audit`, `figures`, `report`, `verify-public`, each as `python -m vfs_research.cli COMMAND`. The VFS `backtest` needs portfolio inputs and the direct KOSPI price/RF benchmark, not FF3 factors. Factor joins are isolated to `factor-test` and supplementary sensitivity diagnostics. The existing lock is immutable; a changed design must receive a new specification and append-only decision. `report` exports VFS's own contiguous observed metrics separately from the locked paired comparison and generates all narrative artifacts from public CSVs. PDF generation additionally uses an available Korean system font with reportlab.

GATE A audits evidence/availability without publishing returns. The remote design commit precedes new outcome computation. All reported performance is PRICE_RETURN_ONLY, gross unless cost is explicitly named. Synthetic values are confined to tests, never public empirical outputs. Public validation recomputes performance, spread, drawdown, CI absence and narrative numbers from monthly aggregate data.

Proprietary raw reconstruction cannot be publicly rerun without the user's authorized datasets. Public aggregate numeric verification is reproducible independently. No claim of unrestricted raw-data reproducibility is made.

## GitHub-only continuation

새 환경에서 이전 비공개 파일 없이 시작하는 절차와 원천 재구축의 검증 상태는 [공개 자료 기반 후속 검증](PUBLIC_SOURCE_REBUILD.md)에 기록했습니다. 기존 공개 성과의 산술 검사와 새 OpenDART 원천에서의 재실행을 구분합니다. 기존 6개월·8개월 결과와 설계는 보존합니다.

## Final publication, preserving original reports

기존 `report`는 최초 보고서 템플릿이다. 현재 최종 원천·사건 패널을 보존하려면 다음 공개 자료 기반 동기화 경로를 사용한다. 결과 CSV를 바꾸면 산술 검사·문서 회귀 검증을 먼저 통과시킨다.

```sh
python -m vfs_research.final_publication
# Korean font + locally rendered chart PNGs are required for PDF regeneration.
python -m vfs_research.pdf_report
python -m vfs_research.reconstruction_report
python -m pytest -q
python -m vfs_research.cli verify-public
```

원천 재실행은 기존 `reconstruction_replay`에 새 `--run-name vfs-vintage-run-<version>`을 지정해 이전 실행을 보존한다. 공식 본문 수집은 `economic_recovery`의 `--workspace`, `--private-dir`, `--selections`에 소유자의 실제 비공개 경로·선별 접수번호 JSON을 준다. 키는 사용하지 않는다. 공개 저장소의 evidence register로 접수번호와 본문 주소를 독립 조회할 수 있지만 원천 권리·월말 경제적 평가는 별도다.

최종 집계는 `final_evidence --workspace <authorized-root> --ff3-root <korea-market> --evidence <private-evidence> --replay <separate-replay> --backup-receipt <private-rehash-receipt>`로 내보낸다. 비공개 receipt는 실제 보관본을 재해시한 file_count/bytes/hash_failures/credentials_included를 담는다. 공개 CI는 private 입력에 접근하지 않고 집계 산술·잠금·수정 금지·NA·공개 문서와 파일만 검증한다. [원천 재실행 증빙](../outputs/final/raw_replay_validation.json).
