# 구형 독립 저장소의 이관 및 삭제 준비 — 2026-10-11 KST

구형 `bucheoncityboy/korea-governance-ff3`는 통합 FF 저장소와 별개의 초기 탐색연구 저장소다. 신규 VFS 저장소로 연구를 모으기 위해 전체 공개 스냅샷 52개 파일을 [legacy_standalone_governance](../legacy_standalone_governance/README.md)에 원래 상대경로와 내용 그대로 보존했다. 통합 저장소에서 먼저 옮긴 133개 파일의 스냅샷도 그대로 유지한다.

**현재 상태: 전체 이관과 로컬 이력 백업 완료, GitHub 저장소 삭제는 최종 승인 대기.** 삭제 완료라고 주장하지 않는다. 원본 미국·한국 FF3를 보존하는 `fama-french-integrated-research`는 삭제 대상이 아니다.

## 보존 근거

- 구형 저장소 main: `664b0fadd19cc89a19fef9f4e814cb7a2d759628`.
- 전체 Git 이력: 2개 커밋, 1개 브랜치, 태그 없음. 모든 ref를 담은 비공개 로컬 mirror와 bundle에 대해 `git fsck --full`, `git bundle verify` 통과.
- bundle SHA256: `fcd4fe923bcf2fba800ed9c21849918623f8b8ba8d37be89bdbf1e1c9851d267`. 이력 bundle은 공개하지 않는다.
- 원본 52개 파일의 Git blob과 SHA256: [이관 명세](standalone_retirement_manifest.csv). 52개 모두 원본과 byte-identical. 기존 신규 저장소에 같은 blob으로 존재한 것은 25개였으며, 27개는 초기 연구의 고유 문서·집계 결과·코드 버전이다.
- CSV 검수: 팩터·포트폴리오 수익률, 연도별 기업 수, 스키마·출처·무결성 감사의 집계다. 원천 종목별 패널, DART 원응답, API 키와 `.env`는 포함하지 않는다. 저작·재배포 검수를 이 snapshot에 한정하며 원천 데이터 권리를 주장하지 않는다.
- Issues/PR과 releases: 현재 각각 0개. 별도 공개 토론 기능은 비활성화 상태다.

구형 `limited / fallback_c`, G 알파 미추정, 초기 기초 FF3 수치와 감사 실패를 수정하거나 새 VFS 성과로 섞지 않았다. 스냅샷의 README는 2026-10-09 시점 기록이다. 현재 연구 상태는 상위 VFS README와 outputs를 따른다. legacy 코드는 새 VFS 엔진이나 Actions 테스트의 실행 대상이 아니다.

## 원래 커밋 이력

```text
664b0fadd19cc89a19fef9f4e814cb7a2d759628 2026-10-09T18:06:01+09:00 Publish FF3 reproduction, governance pipeline, tests and limited research results
9f4dd7385af2ce2830261b4b1bd22bc0617f4661 2026-10-09T17:56:26+09:00 Publish Korean FF3 governance research overview
```

## 포트폴리오 실제 반영

[portfolio-index PR #1](https://github.com/bucheoncityboy/portfolio-index/pull/1)을 사용자 요청에 따라 병합했다. 공개 main의 merge commit은 [`f3e9afe166613c4fc61f20c02356428b56d1931d`](https://github.com/bucheoncityboy/portfolio-index/commit/f3e9afe166613c4fc61f20c02356428b56d1931d)이다. 개인 연구 한 행만 VFS로 교체했고 교내 FF3 학회 연구는 보존했다. 신규 저장소·연구 PDF·Pages 링크가 실제 공개 README에 표시되는 것을 확인했다.
