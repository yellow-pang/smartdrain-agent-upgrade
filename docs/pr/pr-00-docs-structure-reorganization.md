# PR 00. Docs Structure Reorganization

## 변경 목적

기존 팀 MVP 산출물과 개인 고도화 프로젝트의 신규 작업 이력을 분리해 문서 탐색성과 유지보수성을 높인다.

## 주요 변경

| 영역 | 내용 |
| --- | --- |
| 문서 구조 | `legacy-mvp`, `reference`, `verification`, `plans`, `steps`, `pr`로 목적별 분리 |
| 문서 인덱스 | `docs/README.md` 추가 |
| 링크 정합성 | root README, frontend README, 기존 frontend 작업 문서의 링크 갱신 |
| 추적 문서 | 이번 구조 개편을 `plan-00`, `step-00`, `pr-00`으로 기록 |

## 리뷰 포인트

- `legacy-mvp/`는 과거 팀 프로젝트 산출물 보관소로 유지한다.
- `reference/`와 `verification/`은 현재 개인 고도화 프로젝트에서 우선 확인할 문서 기준이다.
- 앞으로 새 작업 이력은 root `docs/plans`, `docs/steps`, `docs/pr`에 작성한다.

## 검증 결과

| 항목 | 결과 |
| --- | --- |
| Markdown 링크 검사 | 통과 |
| 예전 루트 docs 번호 경로 검색 | 통과 |
| Compose config 검사 | 통과 |

## 남은 위험

- 과거 frontend 작업 이력 문서는 작성 당시 맥락을 유지하므로, 현재 구현 기준과 다른 표현이 일부 남아 있을 수 있다.
- Git stage 전에는 파일 이동이 delete/add로 표시될 수 있으므로, 커밋 전 rename 인식 여부를 확인한다.
