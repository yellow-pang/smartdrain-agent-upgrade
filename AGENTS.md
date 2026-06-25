# SmartDrain Codex Guidelines

SmartDrain은 팀 프로젝트 MVP에서 출발했지만, 현재 저장소는 개인 Fork 기반의 아키텍처 리팩터링과 기능 고도화를 진행하는 작업 공간입니다. Codex는 기존 MVP의 맥락을 존중하되, 새 변경은 개인 고도화 프로젝트의 유지보수성, 실행 재현성, AI 에이전트 확장성을 기준으로 판단합니다.

## 작업 기준

- 작업 전 `git status --short --branch`로 브랜치와 미커밋 변경을 확인합니다.
- 실제 파일 구조와 스크립트를 먼저 확인하고, 문서와 코드가 다르면 코드 기준으로 판단합니다.
- 사용자 변경으로 보이는 파일은 되돌리지 않습니다.
- 루트 구조는 `frontend/`, `backend/`, `ai_service/`의 책임 분리를 우선합니다.
- 문서 변경은 현재 구현과 앞으로의 리팩터링 방향을 구분해 적습니다.
- 실제 `git commit`, `git push`는 사용자가 직접 진행합니다.

## 프로젝트 구조 책임

| 경로 | 책임 |
| --- | --- |
| `frontend/` | Next.js 관리자 대시보드, 지도/차트/상세 화면, 브라우저 공개 환경변수 |
| `backend/` | FastAPI API 서버, DB 모델, Alembic migration, WebSocket, AI callback |
| `ai_service/` | 비동기 AI 분석 서버, YOLO/OpenCV, XGBoost, Backend callback |
| `ai-vision/` | 모델 학습, PoC, 실험 코드와 산출물 |
| `mock_data/` | 로컬/시연용 샘플 이미지와 데이터 |
| `nginx/` | same-origin reverse proxy 설정 |
| `docs/` | 원 MVP 산출물과 전체 아키텍처/요구사항 문서 |
| `.jenkins/`, `jenkins/` | CI/CD와 배포 보조 파일 |

## Frontend 작업

- Next.js App Router, TypeScript, React 함수형 컴포넌트를 사용합니다.
- `frontend/package.json`의 scripts를 확인한 뒤 `pnpm lint`, `pnpm build`, `pnpm exec tsc --noEmit` 중 필요한 검증을 실행합니다.
- 컴포넌트 파일은 lowercase kebab-case, export 이름은 PascalCase를 사용합니다.
- Tailwind CSS와 `components/ui/`의 기존 primitive를 우선 사용합니다.
- API base URL은 same-origin이면 비워 두고, 직접 backend를 호출하는 로컬 개발에서만 `NEXT_PUBLIC_API_BASE_URL`을 사용합니다.

## Backend 작업

- backend 단독 실행 기준 파일은 `backend/` 아래에 둡니다.
- Alembic 설정은 `backend/alembic.ini`, migration 파일은 `backend/alembic/`을 기준으로 합니다.
- 런타임 의존성은 `backend/requirements.txt`를 기준으로 관리합니다.
- REST, WebSocket, callback 계약 변경 시 frontend adapter와 README/API 문서를 함께 점검합니다.

## AI Service 작업

- AI 서버 런타임 의존성은 `ai_service/requirements.txt`를 기준으로 관리합니다.
- YOLO/XGBoost 모델 계층은 HTTP callback 정책을 알지 않도록 유지합니다.
- Backend callback, timeout, retry, HTTP 오류 매핑은 `ai_service/http` 계층에서 다룹니다.
- 실제 모델 파일과 비밀값은 Git에 커밋하지 않습니다.

## 문서 작성 기준

- 루트 `README.md`는 포트폴리오용 대표 문서이자 전체 실행 안내입니다.
- 하위 README는 각 서비스 담당자가 바로 실행/검증할 수 있는 운영 노트로 유지합니다.
- 오래된 팀 프로젝트 표현, 절대 로컬 경로, 현재 구조와 다른 명령어는 발견 시 함께 정리합니다.
- 문서는 기본적으로 한국어로 작성하고, 명령어는 Windows PowerShell과 Docker Compose 기준을 우선 안내합니다.

## 검증과 보고

- 변경 범위에 맞는 최소 검증을 실행하고, 실행하지 못한 검증은 이유를 남깁니다.
- 최종 보고에는 변경 요약, 검증 결과, 남은 리스크를 포함합니다.
- 가능한 경우 한글 Conventional Commit 메시지를 제안합니다.
