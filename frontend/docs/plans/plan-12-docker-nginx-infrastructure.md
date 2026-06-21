# 12 Docker Compose 및 Nginx 단일 진입점 구성 계획

## 1. 작업 개요

| 항목        | 내용                                                                                                                                                |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| 현재 브랜치 | `infra/docker-nginx-setting`                                                                                                                        |
| 작업 규모   | 큰 작업 — `/frontend` 밖 Dockerfile, 루트 `docker-compose.yml`, Nginx 설정 및 환경변수 구성이 포함됨                                                |
| 최종 목표   | 프런트엔드, 백엔드, AI 서비스, PostgreSQL을 Docker Compose로 기동하고 Nginx의 단일 host/port로 HTTP와 WebSocket을 제공                              |
| 이번 범위   | `frontend/Dockerfile`, `backend/Dockerfile`, `ai_service/Dockerfile`, `nginx/` 설정, 루트 `docker-compose.yml`, 필요한 `.dockerignore` 및 실행 문서 |
| 비목표      | 실제 YOLO/XGBoost 모델 배포, TLS 인증서 발급, Kubernetes, CI/CD, 외부 도메인 연결                                                                   |

> [용어 설명]
>
> - 단일 host/port는 여러 서비스가 실행되더라도 사용자는 하나의 주소와 포트(예: `http://localhost:80`)로만 접속하는 구조입니다.
> - WebSocket은 브라우저와 서버가 연결을 유지하며 실시간으로 양방향 데이터를 주고받는 통신 방식입니다.
> - TLS 인증서는 HTTP 연결을 HTTPS로 암호화하는 인증서입니다.

## 용어 빠른 참조

| 용어                         | 설명                                                                                                                             |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Reverse proxy(역방향 프록시) | 외부 요청을 먼저 받아 내부의 실제 서비스로 알맞게 전달하는 중개 서버입니다. 이번 구성에서는 Nginx가 이 역할을 합니다.            |
| Same-Origin(동일 출처)       | 브라우저가 보는 프로토콜·도메인·포트가 같은 상태입니다. Nginx 하나로 접근하면 CORS 문제를 줄일 수 있습니다.                      |
| Docker Compose               | 여러 컨테이너의 이미지, 네트워크, 환경변수, 실행 순서를 YAML 파일로 함께 관리하는 도구입니다.                                    |
| Container DNS(컨테이너 DNS)  | Compose 네트워크 안에서 서비스 이름(`db`, `backend`)으로 서로를 찾는 이름 해석 기능입니다.                                       |
| Healthcheck(헬스체크)        | 컨테이너가 단순 실행 중인지가 아니라 실제 요청을 처리할 준비가 됐는지 주기적으로 검사하는 설정입니다.                            |
| Migration(마이그레이션)      | 코드 변경에 맞춰 기존 데이터베이스 테이블 구조를 안전하게 최신 상태로 바꾸는 과정입니다. 이 프로젝트에서는 Alembic을 사용합니다. |
| Seed / Opt-in                | Seed는 개발용 초기 데이터이고, opt-in은 사용자가 명시한 경우에만 실행하는 안전한 기본 정책입니다.                                |
| Build argument(빌드 인자)    | Docker 이미지를 만드는 순간에만 전달하는 값입니다. Next.js의 `NEXT_PUBLIC_*` 값은 이때 브라우저 코드에 포함됩니다.               |
| Bind mount / Hot Reload      | Bind mount는 로컬 소스를 컨테이너에 연결하는 방식이고, Hot Reload는 코드 저장 뒤 서버/화면을 자동 갱신하는 개발 기능입니다.      |

## 2. 현재 상태 확인 결과

| 영역          | 현재 상태                                                                                                  | 컨테이너화 시 처리                                                                                               |
| ------------- | ---------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Compose       | PostgreSQL 16 단일 서비스와 named volume만 존재                                                            | 애플리케이션 3개와 Nginx를 추가하고 서비스 의존성 및 healthcheck를 정의                                          |
| Frontend      | Next.js 16, `pnpm-lock.yaml` 존재, API URL은 `NEXT_PUBLIC_API_BASE_URL`, WebSocket URL은 해당 URL에서 파생 | production build/`next start` 컨테이너를 만들고 브라우저 기준 같은 origin 경로를 사용하도록 URL 처리 방식을 확정 |
| Backend       | FastAPI, 루트 `requirements.txt`, 기본 DB/AI 주소가 `localhost`                                            | 컨테이너 DNS인 `db`, `ai-service`를 환경변수로 주입하고 startup readiness를 보장                                 |
| AI Service    | FastAPI, `ai_service/requirements.txt`, callback 대상 기본값이 `localhost:8000`                            | callback 대상은 내부 네트워크의 `backend:8000`으로 설정                                                          |
| Database      | PostgreSQL 16, 데이터 영속 volume 존재                                                                     | healthcheck 추가, 백엔드 기동 전에 ready 상태를 확인                                                             |
| Reverse proxy | 없음                                                                                                       | Nginx가 정적/Next 요청, `/api/`, `/docs`, `/openapi.json`, `/ws/`를 각각 적절한 upstream으로 전달                |

> [용어 설명]
>
> - named volume은 컨테이너를 삭제해도 DB 데이터를 유지하는 Docker 저장 공간입니다.
> - production build는 배포용으로 코드를 최적화하는 과정입니다.
> - startup readiness는 프로세스가 켜진 상태를 넘어 DB 연결 등을 마치고 실제 요청을 처리할 준비가 된 상태입니다.
> - callback은 AI 서버가 분석 완료 후 백엔드로 결과를 다시 보내는 역방향 요청입니다. upstream은 Nginx가 요청을 전달하는 뒤편의 실제 서비스입니다.

현재 코드에서 특별히 확인한 점:

1. 백엔드는 `/api/*` REST API와 `/ws/drains/status` WebSocket을 제공한다.
2. AI는 `/ai/analysis/run`을 제공하지만, 정상 흐름에서는 백엔드가 Docker 내부에서 호출한다. 브라우저 공개는 필수가 아니다.
3. 프런트 WebSocket helper는 현재 절대 HTTP(S) API URL을 WebSocket URL로 변환한다. Nginx 단일 origin을 쓰려면 API를 `/api` 상대 경로로 둘 때의 WebSocket URL 생성 규칙을 보완해야 한다.
4. Next.js의 `NEXT_PUBLIC_*` 값은 클라이언트 번들 빌드 시 반영되므로, Docker build argument/환경변수 전략을 고정해야 한다.

> [용어 설명]
>
> - 클라이언트 번들은 브라우저가 실행할 수 있도록 프런트 코드를 묶은 결과물입니다.
> - Next.js의 `NEXT_PUBLIC_*` 값은 `next build` 시점에 이 결과물에 포함되므로, 컨테이너 실행 후 환경변수만 바꿔서는 값이 바뀌지 않습니다.

## 3. 목표 아키텍처

```text
Browser
  └─ http://localhost[:HOST_PORT] (Nginx)
       ├─ /, /drains/*       → frontend:3000 (Next.js)
       ├─ /api/*, /docs,*    → backend:8000 (FastAPI)
       └─ /ws/*              → backend:8000 (WebSocket Upgrade)

backend:8000 ── HTTP ──> ai-service:9000
ai-service:9000 ─ HTTP callback ─> backend:8000
backend:8000 ── PostgreSQL ──> db:5432 (named volume)
```

외부 브라우저는 Nginx만 접속합니다. 서비스 간 통신은 Compose 기본 네트워크의 서비스 이름을 사용하므로, 컨테이너 내부에서 `localhost`를 다른 서비스 주소로 사용하지 않습니다.

## 4. 변경 설계

### 4.1 Docker 이미지

| 대상       | 계획                                                                                                      | 핵심 사항                                                                                                 |
| ---------- | --------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Frontend   | Node LTS 기반 multi-stage build (`pnpm install --frozen-lockfile` → `next build` → `next start`)          | `NEXT_PUBLIC_API_BASE_URL=/api`를 build arg로 주입하고 불필요한 dev 의존성/소스를 runtime 이미지에서 제외 |
| Backend    | Python slim 기반 이미지, `backend/requirements.txt` 설치 후 `uvicorn app.main:app --host 0.0.0.0 --port 8000` 실행 | build context는 루트를 유지하되, 현재 stub 기반 백엔드에 불필요한 YOLO/CUDA 의존성은 제외해 이미지 크기와 빌드 시간을 줄임 |
| AI Service | Python slim 기반 이미지, `ai_service/requirements.txt` 설치 후 `uvicorn ai_service.http.app:app` 실행     | import 경로를 위해 프로젝트 루트를 컨테이너에 유지하고 9000 포트만 내부 노출                              |
| Nginx      | 공식 Nginx Alpine 이미지에 프로젝트 설정만 복사                                                           | upstream DNS resolver, proxy timeout, WebSocket `Upgrade`/`Connection` 헤더 포함                          |

각 서비스별 `.dockerignore` 또는 루트 `.dockerignore`에는 `node_modules`, `.next`, Python virtualenv/cache, `.git`, 테스트 산출물 등을 제외해 빌드 컨텍스트를 줄입니다.

> [용어 설명]
>
> - Node LTS는 장기간 안정성과 보안 업데이트를 지원하는 Node.js 버전입니다.
> - multi-stage build는 빌드용 도구와 실제 실행 이미지를 분리해 최종 이미지 크기와 노출을 줄이는 방식입니다. `--frozen-lockfile`은 lockfile에 고정된 버전 그대로만 설치하게 해 팀원·CI 환경의 차이를 막습니다.
> - build context는 Docker 빌드에 전달되는 파일 범위이며, Alpine은 매우 작은 Linux 기반 이미지입니다.

### 4.2 Compose 서비스와 환경변수

| 서비스       | 환경/의존성                                                                                                                             | 외부 노출 계획                       |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| `db`         | `POSTGRES_*`, `postgres_data` volume, `pg_isready` healthcheck                                                                          | 기본적으로 비공개                    |
| `backend`    | `DATABASE_URL=...@db:5432/...`, `AI_SERVER_BASE_URL=http://ai-service:9000`, `AI_CALLBACK_BASE_URL=http://backend:8000`, `CORS_ORIGINS` | Nginx 경유만, 직접 port publish 없음 |
| `ai-service` | `BACKEND_BASE_URL=http://backend:8000`                                                                                                  | Nginx 경유만, 직접 port publish 없음 |
| `frontend`   | build arg `NEXT_PUBLIC_API_BASE_URL=/api`                                                                                               | Nginx 경유만, 직접 port publish 없음 |
| `nginx`      | frontend/backend upstream, 외부 host port                                                                                               | 유일한 기본 공개 서비스              |

`depends_on.condition: service_healthy`는 DB 준비에 적용합니다. 단, Compose 의존성만으로 마이그레이션 완료까지 보장할 수 없으므로 DB 초기화 방식은 아래 확인 항목에서 결정합니다.

> [용어 설명]
>
> - port publish는 컨테이너 포트를 PC 외부 포트와 연결해 직접 접속을 허용하는 설정입니다.
> - `depends_on.condition: service_healthy`는 DB 컨테이너가 실행됐다는 사실만이 아니라 healthcheck를 통과한 뒤 다음 서비스를 시작하게 합니다.

### 4.3 Nginx 라우팅 정책

| 외부 경로                          | 대상            | 처리                                                            |
| ---------------------------------- | --------------- | --------------------------------------------------------------- |
| `/` 및 Next.js 페이지/asset        | `frontend:3000` | `Host`, `X-Forwarded-*` 전달                                    |
| `/api/`                            | `backend:8000`  | API prefix 유지, 일반 HTTP proxy                                |
| `/ws/`                             | `backend:8000`  | HTTP/1.1, `Upgrade`, `Connection` 헤더와 장기 read timeout 적용 |
| `/docs`, `/redoc`, `/openapi.json` | `backend:8000`  | FastAPI 문서/스키마 접근 허용 여부를 사용자 결정에 따라 구성    |
| `/ai/`                             | 기본 비공개     | 운영자 직접 접근이 필요한 경우에만 명시적으로 proxy route 추가  |

Nginx가 same-origin을 제공하므로 브라우저의 REST 요청은 `/api`로, WebSocket은 현재 페이지 protocol/host 기준 `ws(s)://<nginx-host>/ws/drains/status`로 연결합니다. 이 경우 개발 환경의 `http://localhost:8000` 설정도 계속 지원하도록 프런트 URL helper는 하위 호환을 유지합니다.

> [용어 설명]
>
> - `X-Forwarded-*` 헤더는 Nginx가 원래 요청의 protocol과 클라이언트 IP 같은 정보를 백엔드에 전달하는 표준 헤더입니다.
> - `Upgrade`와 `Connection` 헤더는 일반 HTTP 연결을 WebSocket 연결로 전환하기 위한 필수 약속입니다.

### 4.4 DB 마이그레이션과 초기 데이터

사용자 결정에 따라 일회성 `migrate` Compose 서비스가 Alembic migration을 자동 실행하고 정상 종료한 뒤 backend가 시작하게 합니다. Mock seed는 개발 편의에는 유용하지만 운영 데이터에 섞이면 안 되므로 `docker compose --profile seed run --rm backend python -m app.seeds.seed_mock_data` 같은 명시적 실행만 허용합니다.

> [용어 설명]
>
> - DDL은 테이블 같은 DB 구조를 생성·수정하는 SQL 명령입니다.
> - profile은 기본 기동에서 제외한 선택 서비스를 그룹으로 묶는 Compose 기능이고, `--rm`은 일회성 작업 컨테이너가 끝난 뒤 자동 삭제하는 옵션입니다.

## 5. 구현 단계

1. Docker build context와 ignore 대상 확정, 서비스별 Dockerfile 작성.
2. Nginx reverse proxy 설정 작성: frontend, REST, Swagger/OpenAPI, WebSocket routing 및 forward header 적용.
3. `docker-compose.yml`을 운영 표준 5개 서비스 구조로 확장하고 `docker-compose.dev.yml`에 bind mount·Hot Reload·개발 전용 문서 공개 정책을 분리: healthcheck, networks, volumes, internal DNS 환경변수, Nginx 단일 port publish 적용.
4. 프런트 API/WebSocket URL helper를 same-origin `/api` + `/ws` 정책에 맞게 최소 변경하고 `.env.example`을 개발/Compose 사용법에 맞춰 보완.
5. 실행 문서에 최초 migration, 선택 seed, 기동/종료, 로그, 주요 확인 URL을 기록.
6. 이미지 build와 Compose 기동 후 HTTP, REST, WebSocket, backend→AI→callback 흐름을 확인하고 결과를 step 문서에 기록.

## 6. 검증 계획

| 검증                                                                    | 기대 결과                                                   |
| ----------------------------------------------------------------------- | ----------------------------------------------------------- |
| `docker compose config`                                                 | Compose 문법과 환경변수 치환이 유효                         |
| `docker compose -f docker-compose.yml -f docker-compose.dev.yml config` | 개발 확장 Compose 병합 결과가 유효                          |
| `docker compose build`                                                  | frontend/backend/AI/Nginx 이미지가 재현 가능하게 build      |
| DB migration                                                            | Alembic head까지 적용                                       |
| `docker compose up -d` 및 `docker compose ps`                           | 모든 장기 실행 서비스가 healthy/running                     |
| `GET /`                                                                 | Nginx 단일 주소에서 Next.js 화면 응답                       |
| `GET /api/...`                                                          | Nginx를 통해 backend API 응답                               |
| `GET /docs`                                                             | 공개 선택 시 FastAPI Swagger 표시                           |
| WebSocket `/ws/drains/status`                                           | Nginx Upgrade 후 연결 및 이벤트 수신                        |
| 비동기 분석                                                             | backend → ai-service → backend callback 후 상태 이벤트 처리 |
| `pnpm lint`, `pnpm build`                                               | 프런트 URL helper 변경에 대한 정적/production 검증          |

## 7. 확정된 구현 결정

사용자 확인을 반영해 아래 항목을 구현 기준으로 확정합니다.

| 결정                    | 확정 내용                                                                         | 적용 이유                                                                                                                                                    |
| ----------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Nginx 외 직접 포트 공개 | Nginx만 `80:80` 공개                                                              | 외부 노출면을 최소화하고 운영과 같은 단일 진입점/Same-Origin 구성을 유지합니다. DB GUI 등 직접 접속은 필요 시 개발 전용 Compose에서만 제한적으로 제공합니다. |
| FastAPI 문서 공개       | 개발 Compose에서는 `/docs`, `/openapi.json` 허용, 운영 Compose에서는 Nginx가 차단 | API 문서는 개발 생산성에는 유용하지만 외부에는 시스템 구조를 노출하므로 운영에서는 닫습니다.                                                                 |
| AI API 공개             | 기본 비공개, backend만 내부 DNS로 호출                                            | 외부 브라우저가 AI API를 직접 호출하지 않도록 서비스 경계를 유지합니다.                                                                                      |
| DB 초기화               | 일회성 `migrate` 서비스가 자동 migration 수행, seed는 수동 opt-in                 | 개발자는 `up`만으로 스키마를 맞출 수 있고, 테스트 데이터는 운영/기존 데이터에 섞이지 않습니다.                                                               |
| 개발/운영 Compose 분리  | `docker-compose.yml`은 운영 표준, `docker-compose.dev.yml`은 개발 확장            | 운영 이미지는 불변으로 유지하고, 개발에서는 bind mount와 Hot Reload를 사용합니다.                                                                            |
| 외부 접속 방식          | 우선 HTTP `localhost:80`                                                          | 도메인과 TLS/HTTPS는 별도 배포 단계에서 추가합니다.                                                                                                          |
| 프런트 환경변수         | Compose build에서는 `NEXT_PUBLIC_API_BASE_URL=/api`                               | REST와 WebSocket 모두 Nginx의 같은 origin을 사용하고, 기존 로컬 절대 URL 개발 방식은 유지합니다.                                                             |

> [용어 설명]
>
> - 노출면은 외부 공격자가 접근할 수 있는 포트·API·관리 화면의 총범위입니다.
> - 불변 이미지는 실행 중 코드가 바뀌지 않는 배포용 이미지입니다.
> - 환경별 Compose 병합은 `docker compose -f docker-compose.yml -f docker-compose.dev.yml up`처럼 운영 기본 설정 위에 개발 설정만 덧붙이는 방식입니다.

## 8. 리스크와 대응

| 리스크                                                           | 대응                                                                                |
| ---------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `localhost`가 컨테이너 자신을 뜻해 서비스 호출이 실패            | 모든 service-to-service URL을 Compose 서비스 DNS로 명시                             |
| WebSocket이 400/502 또는 즉시 close                              | Nginx HTTP/1.1 Upgrade header와 `/ws/` location을 별도 설정하고 실제 handshake 검증 |
| Next.js public env가 런타임에 바뀌지 않음                        | API public URL을 build arg로 고정하고 build 재실행 필요성을 문서화                  |
| DB가 준비되기 전에 backend가 연결 시도                           | DB healthcheck와 backend dependency를 설정하고 migration 절차를 분리                |
| 자동 seed가 반복/운영 데이터를 오염                              | seed를 profile/명령으로 opt-in 처리                                                 |
| AI의 현재 fake predictor가 실제 모델로 바뀔 때 이미지가 비대해짐 | 현재는 경량 FastAPI 이미지로 두고 CUDA/모델 artifact는 후속 전용 이미지 설계로 분리 |
| 백엔드가 루트 ML requirements를 설치해 이미지가 비대해짐 | 현재 backend 실행 코드에 필요한 의존성만 `backend/requirements.txt`로 분리하고, 실제 모델 의존성은 AI 전용 이미지 도입 시 추가 |

> [용어 설명]
>
> - handshake는 WebSocket 같은 연결을 시작하기 전에 클라이언트와 서버가 통신 가능 여부를 확인하는 사전 교환입니다.
> - CUDA는 NVIDIA GPU로 AI 연산을 가속하는 플랫폼이고, artifact는 학습이 끝난 모델 파일 같은 배포 산출물입니다.

## 9. 이번 턴 실행 범위

1. `frontend/AGENTS.md`, 문서화 규칙, 최신 plan, 시스템 아키텍처, 현재 Compose 및 서비스 설정을 확인했다.
2. 서비스별 Dockerfile, Nginx 운영/개발 설정, 운영/개발 Compose, 환경변수 및 프런트 WebSocket helper를 구현했다.
3. Docker 통합 검증 결과는 `../steps/step-14-docker-nginx-infrastructure.md`에 기록했다.

## 10. 승인 후 제안 커밋 메시지

```text
feat: Docker Compose와 Nginx 단일 진입점 구성
```

```text
- 프런트엔드, 백엔드, AI 서비스의 컨테이너 이미지를 추가한다.
- Nginx가 웹 화면, API, WebSocket 요청을 단일 주소로 라우팅한다.
- 컨테이너 서비스 간 DB와 AI callback 주소를 내부 DNS로 분리한다.
- 기동, 마이그레이션, 선택 seed 및 검증 절차를 문서화한다.
```
