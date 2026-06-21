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

개발 Compose는 Hot Reload와 FastAPI 문서를 포함하며 Nginx의 `8080` 포트로 접속합니다.

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
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

| 구분           | 명령                                                                        | 공개 포트 | 특징                                              |
| -------------- | --------------------------------------------------------------------------- | --------- | ------------------------------------------------- |
| 개발           | `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build` | `8080`    | 소스 bind mount, Hot Reload, `/docs` 허용         |
| 운영 기준 검증 | `docker compose up --build -d`                                              | `80`      | production image, Nginx만 외부 공개, `/docs` 차단 |

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
