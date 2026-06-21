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

## 환경변수 및 CI/CD 확장 정리

### 환경변수 책임 분리

기존 root `.env`는 backend 설정 파일로도 읽혔지만 Docker Compose는 이를 직접 사용하지 않아 책임이 섞여 있었다. 이번에 root `.env`를 Compose/배포 입력값으로 전환하고, backend 설정은 `backend/.env`, AI 설정은 `ai_service/.env`로 분리했다.

| 위치 | 책임 | 예시 파일 | 비밀값 저장 여부 |
| --- | --- | --- | --- |
| `/.env` | Compose project 이름, host port, DB 컨테이너 값, Compose가 주입하는 backend/AI 설정 | `/.env.example` | 로컬·Jenkins VM만 사용. 운영 비밀값은 저장하지 않음 |
| `/backend/.env` | Docker 없이 backend를 실행할 때의 DB, CORS, AI URL | `/backend/.env.example` | 로컬 개발 전용 |
| `/ai_service/.env` | Docker 없이 AI를 실행할 때의 backend callback URL | `/ai_service/.env.example` | 로컬 개발 전용 |
| `/frontend/.env.local` | 브라우저 공개 API URL과 Kakao JavaScript 키 | `/frontend/.env.example` | 공개 가능한 값만 저장 |

backend는 더 이상 root `.env`를 읽지 않으며 `backend/.env`만 읽는다. AI 서비스는 `ai_service/.env`를 자동으로 읽되, Docker Compose가 전달한 환경변수가 우선한다.

### AWS, Vercel, CI/CD 적용 기준

| 대상 | 지금 준비한 사항 | 실제 연결 시 할 일 |
| --- | --- | --- |
| AWS | Compose 값에 `${VARIABLE}` 치환과 port/DB 연결 변수 분리를 적용 | RDS 접속 정보, 배포 키는 AWS Secrets Manager에 보관하고 ECS/EC2 배포 시 secret 참조로 주입 |
| Vercel | frontend 공개 변수와 same-origin `/api` 정책을 구분 | Vercel 환경변수에 `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_KAKAO_MAP_APP_KEY`를 환경별 등록하고 Kakao 허용 도메인 추가 |
| GitHub Actions | Docker context에서 `.github/`와 secret 파일을 제외 | Actions Secrets에는 AWS 자격증명·배포용 secret, Variables에는 리전·이미지 이름처럼 비밀이 아닌 값 저장 |
| Jenkins + 개인 Notebook VM | Jenkins/notebook 경로를 Docker context에서 제외 | Jenkins는 개발 검증/이미지 build만 담당하고, Notebook VM의 데이터·노트북·자격증명은 애플리케이션 이미지에 넣지 않음 |

`NEXT_PUBLIC_*` 변수는 브라우저 코드에 포함되므로 AWS access key, DB URL, 비밀번호, webhook secret처럼 비밀인 값에는 절대 사용하지 않는다.

### Docker build context 제외 정책

`.dockerignore`에 기존 docs·node_modules·Python cache 외에 아래 항목을 추가했다.

```text
.github/ .jenkins/ jenkins/ Jenkinsfile
notebook/ notebooks/ *.ipynb **/.ipynb_checkpoints/
terraform/ infra/ k8s/ kubernetes/ helm/ ansible/
.aws/ *.pem *.key *.crt secrets/
```

이는 CI/CD 정의, 개인 Notebook VM 산출물, IaC, AWS 자격증명, 인증서가 애플리케이션 Docker 이미지에 실수로 포함되는 것을 막는다. 향후 Docker build에 IaC 또는 배포 스크립트가 실제로 필요해지면 해당 파일 전체를 허용하지 말고, 필요한 파일만 별도 build context 또는 artifact로 전달한다.

## 이번 추가 검증

| 검증 | 결과 |
| --- | --- |
| 운영 Compose 환경변수 치환 `docker compose config --quiet` | 통과 |
| 개발 Compose 환경변수 치환 `docker compose -f docker-compose.yml -f docker-compose.dev.yml config --quiet` | 통과 |
| `docker compose build ai-service` | 통과 — `python-dotenv`을 포함한 AI 이미지 재빌드 성공 |

## README 및 개발·운영 가이드 보강

루트 README를 프로젝트 소개, 구성도, Docker 빠른 시작, 개발/운영 테스트 구분, 환경변수 원칙, 배포 방향을 포함한 첫 진입 문서로 재구성했다. 생성형 AI 도구가 일부 설정과 문서 초안에 사용됐다는 고지도 추가했다.

`docs/deployment/development-production-guide.md`에는 VirtualBox Ubuntu·Jenkins·Cloudflare 개발 환경과 AWS·GitHub Actions·Vercel 운영 환경, EC2 Compose에서 RDS/ECS로 확장하는 인턴 프로젝트 기준, 테스트·secret 관리·배포 체크리스트를 기록했다.

## frontend Docker·로컬 환경변수 우선순위 정리

Docker 개발 컨테이너는 frontend 폴더를 bind mount하므로 팀원의 `frontend/.env.local`이 함께 보인다. 이 파일의 `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`이 Docker same-origin API 설정과 섞이면 브라우저가 공개되지 않은 host port로 요청해 loading skeleton이 유지될 수 있다.

이를 막기 위해 root `.env`에는 Compose 전용 `COMPOSE_FRONTEND_API_BASE_URL`, `COMPOSE_FRONTEND_KAKAO_MAP_APP_KEY`를 선언하고, Compose는 이 두 공개 값만 frontend에 전달한다. `next.config.mjs`는 Compose 실행일 때 해당 값을 `NEXT_PUBLIC_*`로 명시 주입한다. Docker 없이 frontend를 실행할 때만 `frontend/.env.local`의 `NEXT_PUBLIC_*`를 사용한다.

개발 Nginx의 `location /`에는 Next.js Hot Reload WebSocket용 `Upgrade`/`Connection` 헤더와 timeout도 추가했다. `/ws/drains/status`는 업무용 backend WebSocket이고, `/_next/webpack-hmr`은 frontend 개발용 HMR WebSocket이라는 점을 구분한다.

same-origin API base는 `/api`가 아니라 빈 값으로 고정했다. 각 API 함수가 이미 `/api/drains`, `/api/dashboard/summary` 같은 전체 경로를 가지고 있어 `/api`를 base로 쓰면 `/api/api/...`라는 잘못된 주소가 만들어진다. 빈 base URL에서도 업무 WebSocket은 현재 브라우저 origin의 `/ws/drains/status`를 사용하도록 보완했다.

## Compose 첫 기동 이미지 pull 오류 수정

`migrate`와 `seed` 서비스가 build 설정 없이 `smartdrain-backend` 이미지 이름만 참조해 첫 `docker compose up --build` 시 Docker Hub pull을 시도하는 문제가 확인됐다. backend와 같은 Dockerfile을 쓰되 `smartdrain-migrate`, `smartdrain-seed`라는 별도 로컬 image tag와 build 설정을 부여했다.

세 이미지는 Docker layer cache를 공유한다. 따라서 외부에 존재하지 않는 `smartdrain-backend` 이미지를 pull하지 않고, 첫 실행에서도 backend/migration/seed 실행 이미지가 로컬에서 만들어진다.

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
