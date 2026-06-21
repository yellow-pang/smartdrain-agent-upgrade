# 14 Docker Compose 및 Nginx 인프라 구성 결과

## 작업 결과

프런트엔드, 백엔드, AI 서비스, PostgreSQL을 Docker Compose로 실행하고 Nginx를 유일한 외부 진입점으로 구성했다.

```text
Browser → Nginx:80 → frontend:3000
                    → backend:8000 (/api, /ws)

backend → ai-service:9000
ai-service → backend callback
backend → db:5432
```

## 변경 파일과 핵심 내용

| 경로 | 변경 내용 |
| --- | --- |
| `.dockerignore` | node_modules, Next build 결과, Python cache 등 불필요한 Docker build context를 제외했다. |
| `frontend/Dockerfile` | pnpm 기반 multi-stage build와 Next.js standalone runtime 이미지를 추가했다. |
| `backend/Dockerfile`, `backend/requirements.txt` | 현재 stub 기반 backend 실행에 필요한 경량 의존성만 분리하고 FastAPI 이미지를 추가했다. |
| `ai_service/Dockerfile`, `ai_service/http/app.py` | AI FastAPI 이미지와 container healthcheck용 `/health` endpoint를 추가했다. |
| `nginx/default.conf` | 운영용 `/`, `/api/`, `/ws/` proxy와 `/docs`, `/openapi.json`, `/redoc` 차단을 설정했다. |
| `nginx/default.dev.conf` | 개발 환경에서만 FastAPI 문서를 Nginx 경유로 허용하도록 분리했다. |
| `docker-compose.yml` | DB healthcheck, 자동 migrate, 내부 DNS 환경변수, Nginx 80 포트 단일 공개, opt-in seed profile을 추가했다. |
| `docker-compose.dev.yml` | bind mount, Hot Reload, 개발 Nginx 8080 포트를 운영 Compose와 분리했다. |
| `frontend/lib/websocket/drain-status-socket.ts` | `/api` 상대 URL일 때 현재 브라우저 origin의 `/ws/drains/status`로 연결하도록 보완했다. |
| `frontend/next.config.mjs` | Docker runtime에 필요한 standalone output을 활성화했다. |
| `.env.example`, `frontend/.env.example`, `README.md` | CORS JSON 배열 형식, 로컬/Compose API URL, 기동·seed·종료 방법을 문서화했다. |

## 핵심 구현 결정

1. 외부에는 Nginx `80:80`만 공개한다. backend, AI, DB, frontend는 Compose 네트워크에서만 통신한다.
2. `migrate`는 DB healthcheck 후 Alembic을 실행하고 종료한다. backend는 migration 성공 후에만 시작한다.
3. `seed`는 기본 기동에서 실행되지 않으며 `docker compose --profile seed run --rm seed`로만 실행한다.
4. Compose에서 리스트 환경변수인 `CORS_ORIGINS`는 Pydantic Settings 호환을 위해 JSON 배열 문자열로 전달한다.
5. root requirements에 있던 CUDA/PyTorch 계열 의존성은 현재 backend의 stub 구현에 필요하지 않아 `backend/requirements.txt`에서 제외했다. 실제 모델 도입 시 AI 전용 이미지에 추가한다.

## 검증 결과

| 검증 | 결과 | 비고 |
| --- | --- | --- |
| `docker compose config --quiet` | 통과 | 운영 Compose 문법 및 병합 값 확인 |
| `docker compose -f docker-compose.yml -f docker-compose.dev.yml config --quiet` | 통과 | 개발용 8080 포트 대체 및 mount 설정 확인 |
| `docker compose build frontend` | 통과 | Docker 내부 Next.js production/standalone build 성공 |
| `docker compose build backend ai-service` | 통과 | 경량 backend 및 AI 이미지 build 성공 |
| `npm.cmd --prefix frontend run lint` | 통과 | 오류 0건, 기존 `<img>` warning 1건 |
| `docker compose up -d` | 통과 | db/backend/ai-service/frontend/nginx 모두 healthy, migrate 정상 종료 |
| `GET http://localhost/` | 통과 | 200 |
| `GET http://localhost/api/dashboard/summary` | 통과 | 200 |
| `GET http://localhost/docs` | 통과 | 운영 Nginx 정책대로 404 |
| `ws://localhost/ws/drains/status` | 통과 | WebSocket 상태 `Open` |

로컬 `npm.cmd --prefix frontend run build`는 기존 `.next` 산출물이 다른 프로세스에 점유되어 `EPERM`으로 실행되지 않았다. 같은 production build는 깨끗한 Docker build context에서 정상 통과했다.

## 실행 방법

운영 방식:

```powershell
docker compose up --build -d
```

개발 방식(Hot Reload, Swagger 허용):

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

## 남은 리스크와 후속 작업

1. 현재는 HTTP 로컬 개발 기준이다. 배포 도메인과 TLS 인증서가 준비되면 Nginx HTTPS, `server_name`, HSTS, WSS를 별도 추가해야 한다.
2. DB 비밀번호는 개발용 고정 값이다. 배포 환경에서는 `.env` 또는 secret manager로 분리해야 한다.
3. 실제 YOLO/XGBoost 모델 도입 시 GPU/CUDA 및 모델 artifact를 backend가 아닌 AI 서비스 이미지에 별도로 설계해야 한다.
4. 테스트 후 컨테이너는 `docker compose down`으로 종료했고 PostgreSQL named volume은 보존했다.

## 추천 커밋 메시지

제목:

```text
feat: Docker Compose와 Nginx 단일 진입점 구성
```

내용:

```text
- 프런트엔드, 백엔드, AI 서비스의 Docker 이미지를 추가한다.
- Nginx가 웹 화면, API, WebSocket 요청을 단일 주소로 라우팅한다.
- 자동 migration과 수동 seed profile을 구성하고 개발용 Compose를 분리한다.
- 컨테이너 내부 DNS 및 CORS 환경변수를 정리하고 실행 절차를 문서화한다.
```
