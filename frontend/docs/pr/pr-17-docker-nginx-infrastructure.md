## PR 제목

[feat] Docker Compose 및 Nginx 단일 진입점 구성

## 작업 내용

- frontend, backend, AI service, PostgreSQL을 Docker Compose로 실행하도록 구성했습니다.
- Nginx가 웹 화면, REST API(`/api/*`), 업무 WebSocket(`/ws/*`)을 단일 주소로 프록시합니다.
- 개발 Compose는 Hot Reload, Swagger, 8080 포트를 제공하고 운영 기준 Compose는 production image와 Nginx 80 포트만 공개합니다.
- DB migration은 `migrate` 일회성 서비스로 자동 실행하고, seed는 opt-in profile로 분리했습니다.
- root Compose 환경변수와 backend/AI/frontend 단독 실행 환경변수를 분리했습니다.
- Next HMR WebSocket, same-origin API base URL, 상세 API 빈 base URL 검증, migration image pull 문제를 수정했습니다.

## 주요 변경 파일

| 구분 | 파일 |
| --- | --- |
| Compose/Nginx | `.dockerignore`, `.env.example`, `docker-compose.yml`, `docker-compose.dev.yml`, `nginx/default.conf`, `nginx/default.dev.conf` |
| Frontend | `frontend/Dockerfile`, `frontend/next.config.mjs`, `frontend/.env.example`, `frontend/lib/api/drain-data.ts`, `frontend/lib/websocket/drain-status-socket.ts` |
| Backend | `backend/Dockerfile`, `backend/requirements.txt`, `backend/.env.example`, `backend/app/core/config.py` |
| AI | `ai_service/Dockerfile`, `ai_service/requirements.txt`, `ai_service/.env.example`, `ai_service/http/app.py`, `ai_service/http/config.py` |
| 문서 | `README.md`, `frontend/docs/plans/plan-12-docker-nginx-infrastructure.md`, `frontend/docs/steps/step-14-docker-nginx-infrastructure.md`, `frontend/docs/deployment/development-production-guide.md` |

## 테스트 결과

| 검증 | 결과 | 비고 |
| --- | --- | --- |
| 운영/개발 Compose config | 통과 | 환경변수 치환과 개발 override 확인 |
| Docker image build | 통과 | frontend, backend, AI, migration image build 확인 |
| Compose 기동 | 통과 | db/backend/AI/frontend/Nginx healthy, migration 정상 종료 |
| Nginx HTTP/API | 통과 | `/`, `/api/drains`, `/api/dashboard/summary` 200 |
| WebSocket | 통과 | `/ws/drains/status`, `/_next/webpack-hmr` 101/Open |
| 상세 API | 통과 | DR-004 상세·센서·위험 이력·분석 endpoint 200 |
| frontend lint | 통과 | error 0건, 기존 native `<img>` warning 1건 |
| `git diff --check` | 통과 | 공백 오류 없음 |

## 리뷰 포인트

- root `alembic.ini`과 root `requirements.txt`는 이번 PR에서 이동하지 않았습니다. 이유와 후속 정리 방안은 step-14의 **`alembic.ini`과 root `requirements.txt` 판단**을 확인해주세요.
- `COMPOSE_FRONTEND_API_BASE_URL`은 Docker same-origin에서 빈 값이 정상입니다. API 함수가 이미 `/api/*` 경로를 포함하므로 `/api`를 base URL로 넣으면 중복 경로가 됩니다.
- 실제 `.env` 파일과 배포 secret은 커밋하지 않습니다. 팀원은 각 `.env.example`을 복사해 사용합니다.

## 비고

- 실제 commit, push, Pull Request 생성, 브랜치 종료는 담당자가 진행합니다.
- AWS/RDS/ECS, Vercel, Cloudflare, Jenkins 확장 기준은 `frontend/docs/deployment/development-production-guide.md`에 정리되어 있습니다.
