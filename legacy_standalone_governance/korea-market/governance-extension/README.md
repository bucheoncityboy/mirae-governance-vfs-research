# Governance extension 실행 모듈

[프로젝트 소개](../../README.md) · [연구노트](output/RESEARCH_NOTE.md) · [상태](output/RESULT_STATUS.json)

저장소 루트에서 `requirements.txt`를 설치한 후 이 디렉터리에서 실행합니다.

```bash
python -m src.pipeline --source ../../.cache/ff3-source
python -m pytest -q tests
```

원본 입력은 쓰지 않습니다. `src/pipeline.py`는 출력 경로가 원본 안에 있거나 원본 커밋이 다르면 실행을 중단합니다. 기본 실행에는 인증키가 필요하지 않으며 `limited / fallback_c` 결과를 생성합니다. G 데이터 수집·실증 입력은 루트 README와 데이터 사전을 참고합니다.
