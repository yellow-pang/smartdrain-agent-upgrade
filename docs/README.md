# SmartDrain Docs

이 디렉터리는 SmartDrain의 문서를 목적별로 분리해 관리합니다. 기존 팀 MVP 산출물과 현재 개인 고도화 프로젝트의 운영 기준, 앞으로 작성할 작업 이력을 섞지 않는 것이 목표입니다.

## 디렉터리 구조

| 경로 | 역할 |
| --- | --- |
| `legacy-mvp/` | 기존 팀 프로젝트 MVP 단계에서 작성된 기획, 요구사항, 설계, PoC, 발표 준비 문서 |
| `legacy-mvp/image/` | MVP 문서에서 사용한 와이어프레임과 아키텍처 참고 이미지 |
| `reference/` | 현재 구현에서도 계속 참조할 API 계약, Backend-AI 연동, AI 모델 artifact 기준 문서 |
| `verification/` | 구현 현황, 통합 테스트, E2E 전략, 배포/운영 런북 등 검증과 운영 기준 문서 |
| `plans/` | 앞으로 작성할 작업 계획 문서 |
| `steps/` | 앞으로 작성할 작업 완료 기록 |
| `pr/` | 앞으로 작성할 PR 요약 문서 |

## 작성 기준

- 새 작업 계획은 `docs/plans/`에 작성합니다.
- 작업 완료 기록은 `docs/steps/`에 작성합니다.
- PR 설명이나 리뷰용 요약은 `docs/pr/`에 작성합니다.
- 기존 MVP 문서는 현재 구현과 다를 수 있으므로, 최신 기준이 필요한 경우 `reference/`와 `verification/` 문서를 우선 확인합니다.
- 과거 문서를 현재 기준으로 직접 덮어쓰기보다, 변경 이유와 현재 기준은 별도 문서나 README에 남깁니다.

## 빠른 링크

| 문서 | 내용 |
| --- | --- |
| [프로젝트 정의](legacy-mvp/01_프로젝트정의서.md) | 기존 MVP의 문제 정의와 목표 |
| [요구사항 정의서](legacy-mvp/03_요구사항정의서.md) | MVP 기능·비기능 요구사항 |
| [시스템 아키텍처](legacy-mvp/06_시스템아키텍처.md) | 초기 시스템 구성과 데이터 흐름 |
| [API 명세](reference/11_API명세서.md) | Frontend·Backend API 계약 |
| [Backend-AI 비동기 분석 API](reference/13_백엔드_AI_서버_비동기_분석_API_정리.md) | AI 분석 요청과 callback 흐름 |
| [AI 모델 아티팩트 관리](reference/15_AI_모델_아티팩트_관리_명세.md) | 모델 파일 공급·검증·교체 기준 |
| [구현 현황과 검증 결과](verification/14_구현현황_및_검증결과.md) | 현재 구현 기준과 확인된 검증 범위 |
| [테스트 전략 및 E2E 검증](verification/16_테스트_전략_및_E2E_검증.md) | 자동/수동 테스트 기준 |
| [배포 운영 런북](verification/17_배포_운영_런북.md) | Compose·Nginx·Jenkins 운영 절차 |
