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
