# SmartDrain

> 지능형 도시 침수 관리 및 모니터링 시스템

SmartDrain은 CCTV 스냅샷과 모의 수위·유속 데이터를 바탕으로 빗물받이의 위험도를 판단하고, 관리자가 지도 기반 대시보드에서 상태와 분석 이력을 확인하는 프로젝트입니다.

## 생성형 AI 활용 고지

- 코드 생성, Docker/Nginx 설정, 문서 작성은 생성형 AI 도구의 보조를 받아 작성했습니다.
- 모든 결과물은 팀원이 요구사항, 보안, 실행 결과를 검토하고 책임지고 반영했습니다.
- 비밀값, 인프라 비용, 배포 권한, 실제 운영 장애 대응은 생성형 도구의 제안만으로 결정하지 않습니다.

## 프로젝트 한눈에 보기

```text
CCTV 스냅샷 + 센서 모의 데이터
        ↓
Backend ──→ AI Service ──→ Backend callback
   ↓
PostgreSQL → WebSocket / REST API → Next.js 관리자 대시보드
```

| 구성 요소     | 기술                         | 책임                                               |
| ------------- | ---------------------------- | -------------------------------------------------- |
| Frontend      | Next.js, React, TypeScript   | 지도 대시보드, 시설 상세, REST/WebSocket 상태 표시 |
| Backend       | FastAPI, SQLAlchemy, Alembic | REST API, DB 저장, AI 요청, WebSocket 이벤트       |
| AI Service    | FastAPI                      | 비동기 분석과 backend callback 계약                |
| Database      | PostgreSQL                   | 시설·센서·분석 결과 영속화                         |
| Reverse proxy | Nginx                        | 웹 화면, `/api`, `/ws` 단일 진입점                 |

## 저장소 구조

```text
frontend/       Next.js 관리자 화면과 frontend 문서
backend/        FastAPI API와 Alembic migration
ai_service/     AI 분석 API와 callback 처리
nginx/          개발/운영 Nginx 설정
docs/           프로젝트 정의와 아키텍처 문서
```

## 빠른 시작: Docker 개발 환경

사전 조건: Docker Desktop 또는 Docker Engine + Compose v2

```powershell
Copy-Item .env.example .env
```

### YOLO 모델 파일 준비

AI 분석까지 실행하려면 Git에 포함하지 않는 `best.pt` 파일이 필요합니다. root `.env`의 `SMARTDRAIN_YOLO_MODEL_PATH`를 **존재하는 파일의 절대 경로**로 바꿉니다. Windows에서는 경로 구분자로 `/`를 사용하면 Compose에서 안전하게 처리됩니다.

```dotenv
SMARTDRAIN_YOLO_MODEL_PATH=C:/smartdrain-data/models/best.pt
```

모델은 읽기 전용으로 AI 컨테이너의 `/app/ai_service/model/best.pt`에 연결됩니다. 파일이 없거나, 일반 파일이 아니거나, 비어 있으면 `ai-service`는 다음 오류를 로그로 남기고 시작하지 않습니다. 모델 없이 분석 결과가 생성되는 상태를 허용하지 않기 위한 정책입니다.

```text
ERROR: YOLO model file is missing, not a regular file, or empty: /app/ai_service/model/best.pt
Set SMARTDRAIN_YOLO_MODEL_PATH in the root .env to an existing best.pt file.
```

확인 명령:

```powershell
$modelPath = (Get-Content .env | Where-Object { $_ -like 'SMARTDRAIN_YOLO_MODEL_PATH=*' } | Select-Object -First 1) -replace '^SMARTDRAIN_YOLO_MODEL_PATH='
Test-Path -LiteralPath $modelPath -PathType Leaf
```

`True`가 나온 뒤에 Compose를 실행합니다. 모델이 아직 없다면 `COMPOSE_AI_SERVER_ENABLED=false`로 backend의 분석 요청을 명시적으로 비활성화할 수 있습니다. 이 경우에도 `ai-service`는 모델 누락 오류를 남기고 종료하지만, frontend·backend·DB의 개발 확인은 계속할 수 있습니다.

개발 Compose는 `mock_data/ai_image_samples`를 AI 컨테이너에 읽기 전용으로 연결합니다. 샘플 이미지를 새로 만들거나 바꾸려면 호스트의 해당 폴더에서 관리하며, 컨테이너 내부에서 수정하지 않습니다.

개발 Compose는 Hot Reload와 FastAPI 문서를 포함하며 Nginx의 `8080` 포트로 접속합니다.

최초 실행 또는 의존성·Dockerfile 변경 시:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

이미 이미지가 생성된 이후 일반적으로 다시 실행할 때는 --build를 제외합니다.

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

소스 코드 수정은 Hot Reload로 반영되므로 이미지 재빌드가 필요하지 않습니다.

AI Service의 의존성이나 Dockerfile이 변경된 경우에만 다음과 같이 해당 서비스만 다시 빌드합니다.

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build --no-deps ai-service
```

| 대상         | 주소                                   |
| ------------ | -------------------------------------- |
| 대시보드     | `http://localhost:8080`                |
| FastAPI 문서 | `http://localhost:8080/docs`           |
| REST API     | `http://localhost:8080/api/...`        |
| WebSocket    | `ws://localhost:8080/ws/drains/status` |

`migrate` 서비스는 DB migration을 한 번 실행하고 종료합니다. 정상 기동 후 개발용 목 데이터가 필요할 때만 아래 명령을 실행합니다.

```powershell
docker compose --profile seed run --rm seed
```

### Cloudflare Tunnel 및 same-origin

운영/개발 VM에서 Cloudflare Tunnel이 `http://127.0.0.1:8099`의 Nginx로 연결되고, 브라우저가 `https://smartdrain.healthq.store`로 접속하는 경우에도 frontend·REST API·WebSocket은 하나의 origin을 사용합니다.

```text
Browser https://smartdrain.healthq.store
  → Cloudflare Tunnel
  → 127.0.0.1:8099 (Nginx)
       ├─ /       → frontend
       ├─ /api/*  → backend
       └─ /ws/*   → backend
```

이 구조에서는 frontend가 backend의 `localhost:8000` 또는 내부 IP를 직접 호출하면 안 됩니다. Compose frontend의 `COMPOSE_FRONTEND_API_BASE_URL`은 빈 값으로 유지합니다. 각 API helper가 이미 `/api/*` 경로를 포함하므로 `/api`를 설정하면 `/api/api/...`가 됩니다. WebSocket helper는 현재 페이지가 HTTPS이면 같은 host의 `wss://…/ws/drains/status`를 자동으로 사용합니다.

same-origin 요청 자체는 CORS 대상이 아니지만, backend를 직접 호출하는 관리 도구 등을 허용해야 한다면 `COMPOSE_CORS_ORIGINS`에 해당 HTTPS origin을 JSON 배열로 설정합니다.

```dotenv
NGINX_HTTP_PORT=127.0.0.1:8099
COMPOSE_CORS_ORIGINS=["https://smartdrain.healthq.store"]
COMPOSE_FRONTEND_API_BASE_URL=
```

### 스케줄러 설정

backend에는 센서 데이터를 기준으로 AI 분석 요청을 만드는 scheduler가 포함돼 있습니다. 로컬 개발 기본값은 예기치 않은 분석 요청을 막기 위해 비활성화(`false`)입니다. 필요한 경우 root `.env`에서 아래 값을 조정한 뒤 backend를 다시 만들거나 재시작합니다.

```dotenv
COMPOSE_ANALYSIS_SCHEDULER_ENABLED=true
COMPOSE_ANALYSIS_SCHEDULER_INTERVAL_SECONDS=300
COMPOSE_ANALYSIS_SCHEDULER_INITIAL_DELAY_SECONDS=60
COMPOSE_ANALYSIS_SENSOR_MAX_AGE_SECONDS=300
COMPOSE_ANALYSIS_JOB_TIMEOUT_SECONDS=600
```

| 변수 | 역할 |
| --- | --- |
| `COMPOSE_ANALYSIS_SCHEDULER_ENABLED` | backend 시작 시 scheduler 실행 여부 |
| `COMPOSE_ANALYSIS_SCHEDULER_INTERVAL_SECONDS` | 분석 대상 탐색 주기 |
| `COMPOSE_ANALYSIS_SCHEDULER_INITIAL_DELAY_SECONDS` | backend 시작 뒤 첫 탐색 전 대기 시간 |
| `COMPOSE_ANALYSIS_SENSOR_MAX_AGE_SECONDS` | 분석 대상으로 인정할 센서 데이터의 최대 경과 시간 |
| `COMPOSE_ANALYSIS_JOB_TIMEOUT_SECONDS` | 처리 중인 분석 job을 실패로 전환하는 timeout |

운영 기준 Compose는 Nginx만 PC의 `80` 포트를 사용합니다. backend·AI·PostgreSQL 포트는 외부에 열지 않으며 `/docs`도 차단합니다.

```powershell
docker compose up --build -d
docker compose ps
```

종료와 로그 확인 명령은 다음과 같습니다.

```powershell
docker compose down
docker compose logs -f nginx backend ai-service
```

`docker compose down -v`는 PostgreSQL volume까지 삭제하므로, 데이터를 초기화할 때만 사용합니다.

## 개발과 운영 실행 방식

| 구분                       | 명령                                                                        | 공개 포트 | 특징                                              |
| -------------------------- | --------------------------------------------------------------------------- | --------- | ------------------------------------------------- |
| 개발 최초 실행·의존성 변경 | `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build` | `8080`    | 이미지 빌드, bind mount, Hot Reload               |
| 개발 일반 실행             | `docker compose -f docker-compose.yml -f docker-compose.dev.yml up`         | `8080`    | 기존 이미지 재사용, 코드 수정 자동 반영           |
| 운영 기준 검증             | `docker compose up --build -d`                                              | `80`      | production image, Nginx만 외부 공개, `/docs` 차단 |

```text
Browser → Nginx:80 → frontend:3000
                    → backend:8000 (/api, /ws)
backend → ai-service:9000 → backend callback
backend → PostgreSQL:5432
```

## 테스트와 확인 방법

테스트는 코드, Docker 이미지, 실행 환경을 나눠 확인합니다.

| 단계                      | 개발 환경                                               | 운영 기준 환경                | 통과 기준                   |
| ------------------------- | ------------------------------------------------------- | ----------------------------- | --------------------------- |
| 정적 검사                 | `npm.cmd --prefix frontend run lint`                    | GitHub Actions에서 동일 실행  | 오류 0건                    |
| Frontend production build | `npm.cmd --prefix frontend run build` 또는 Docker build | Docker/GitHub Actions build   | Next.js build 성공          |
| AI 단위·계약 테스트       | `python -m pytest ai_service`                           | CI에서 동일 실행              | callback/분석 계약 통과     |
| Compose 설정              | 개발 Compose `config --quiet`                           | 운영 Compose `config --quiet` | 문법·환경변수 유효          |
| 통합 smoke test           | 개발 주소에서 화면·API·WebSocket 확인                   | 운영 Nginx 경유 확인          | `/`, `/api`, WebSocket 연결 |

현재 backend 전용 자동 테스트는 별도로 구성되어 있지 않습니다. API 변경 시 FastAPI 문서 또는 통합 테스트로 확인하고, backend pytest/API smoke test는 후속 과제로 관리합니다.

## 환경변수와 배포 설정 분리

환경변수는 실행 주체별로 분리한다. 실제 `.env` 파일은 Git과 Docker build context에 포함되지 않는다.

| 파일                   | 책임                                                   | 사용하는 환경                   |
| ---------------------- | ------------------------------------------------------ | ------------------------------- |
| `/.env`                | Compose project/port/DB 연결 문자열 등 배포 입력값     | Docker Compose, Jenkins 개발 VM |
| `/backend/.env`        | Docker 없이 FastAPI를 로컬 실행할 때의 backend 설정    | backend 로컬 개발               |
| `/ai_service/.env`     | Docker 없이 AI 서비스를 로컬 실행할 때의 callback 설정 | AI 로컬 개발                    |
| `/frontend/.env.local` | Next.js 로컬 실행용 공개 API URL·Kakao JavaScript 키   | frontend 로컬 개발              |

각 서비스의 예시 파일을 복사해 사용한다.

```powershell
Copy-Item .env.example .env
Copy-Item backend\.env.example backend\.env
Copy-Item ai_service\.env.example ai_service\.env
Copy-Item frontend\.env.example frontend\.env.local
```

운영 비밀값(데이터베이스 비밀번호, 배포 접근 키)은 `.env` 파일이나 GitHub 저장소에 저장하지 않는다. AWS에서는 Secrets Manager 또는 ECS task definition의 secret 참조를 사용하고, GitHub Actions에서는 Secrets에 저장해 배포 단계에서만 주입한다.

Vercel에는 frontend에서 실제 사용하는 공개 변수만 등록한다.

- `NEXT_PUBLIC_API_BASE_URL`: API가 별도 도메인이라면 해당 HTTPS URL, Nginx와 같은 origin이면 `/api`
- `NEXT_PUBLIC_KAKAO_MAP_APP_KEY`: 브라우저에서 사용하는 JavaScript 키이며, Kakao Developers의 허용 도메인도 Vercel 도메인으로 추가

`NEXT_PUBLIC_*` 값은 브라우저 번들에 포함되므로 비밀번호·AWS 키·DB URL 같은 비밀값을 넣으면 안 된다.

Docker Compose는 root `.env`의 `COMPOSE_FRONTEND_API_BASE_URL`과 `COMPOSE_FRONTEND_KAKAO_MAP_APP_KEY`만 frontend에 전달합니다. `COMPOSE_FRONTEND_API_BASE_URL`을 빈 값으로 두면 브라우저와 Nginx의 same-origin을 사용하며, API 함수가 포함한 `/api/*` 경로를 그대로 요청합니다. frontend의 `.env.local`은 Docker 없이 `pnpm dev`를 실행할 때만 사용하며, 이때는 `http://localhost:8000`처럼 backend 직접 주소를 설정합니다.

## 배포 방향

```text
개발: 개인 VirtualBox Ubuntu + Jenkins + Cloudflare 개발 서브도메인
운영: Vercel frontend + AWS backend/AI/DB + GitHub Actions + Cloudflare 운영 서브도메인
```

상세 운영 가이드와 Cloudflare 서브도메인, AWS/RDS 범위 선택은 [개발·운영 배포 가이드](frontend/docs/deployment/development-production-guide.md)를 확인하세요.

## 주요 문서

| 문서                                                                                 | 내용                               |
| ------------------------------------------------------------------------------------ | ---------------------------------- |
| [시스템 아키텍처](docs/06_시스템아키텍처.md)                                         | 시스템 구성과 MVP 데이터 흐름      |
| [API 명세](docs/11_API명세서.md)                                                     | frontend-backend API 계약          |
| [Docker/Nginx 작업 결과](frontend/docs/steps/step-14-docker-nginx-infrastructure.md) | 컨테이너 구성, 환경변수, 검증 결과 |
| [개발·운영 배포 가이드](frontend/docs/deployment/development-production-guide.md)    | 팀 개발/운영/CI/CD 가이드          |
