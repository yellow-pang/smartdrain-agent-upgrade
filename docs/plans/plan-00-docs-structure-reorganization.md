# Plan 00. Docs Structure Reorganization

## 목적

기존 팀 MVP 단계에서 작성된 개발 문서와 앞으로 개인 고도화 과정에서 새로 작성할 `plans`, `steps`, `pr` 문서가 섞이지 않도록 루트 `docs/` 구조를 목적별로 분리한다.

## 배경

기존 `docs/`에는 프로젝트 정의, 요구사항, 아키텍처, API 명세, 검증 결과, 운영 런북이 번호 문서로 한곳에 모여 있었다. 이 상태에서 새 작업 계획과 PR 기록을 같은 위치에 추가하면 과거 MVP 산출물과 현재 개인 고도화 이력이 구분되지 않는다.

## 변경 계획

| Phase | 작업 | 대상 |
| --- | --- | --- |
| 1 | 기존 MVP 산출물 분리 | `docs/01_*` ~ `docs/10_*`, `docs/image/` |
| 2 | 현재 참조 문서 분리 | API 명세, Backend-AI 연동, AI 모델 artifact 문서 |
| 3 | 검증·운영 문서 분리 | 통합 테스트, 구현 현황, 테스트 전략, 운영 런북 |
| 4 | 신규 작업 이력 폴더 생성 | `docs/plans/`, `docs/steps/`, `docs/pr/` |
| 5 | 링크와 인덱스 정리 | `docs/README.md`, root README, 관련 frontend 문서 |

## 목표 구조

```text
docs/
├─ README.md
├─ legacy-mvp/
├─ reference/
├─ verification/
├─ plans/
├─ steps/
└─ pr/
```

## 검증 계획

- Markdown 상대 링크가 실제 파일을 가리키는지 확인한다.
- 예전 `docs/01_*` ~ `docs/17_*` 루트 경로 참조가 남았는지 검색한다.
- Compose 설정에는 영향이 없는지 `docker compose -f docker-compose.yml -f docker-compose.dev.yml config --quiet`로 확인한다.

## 남은 위험

- 과거 frontend 작업 이력 문서에는 작성 당시 기준의 경로와 설명이 남아 있을 수 있다.
- Git stage 전에는 파일 이동이 rename이 아니라 delete/add로 보일 수 있다.
