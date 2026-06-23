# 22 로컬 Docker Compose 개발 환경 정비 계획

## 1. 작업 개요

| 항목 | 내용 |
| --- | --- |
| 작업 브랜치 | `infra/docker-compose-update` |
| 작업 규모 | 큰 작업 — 루트 Compose·Nginx·환경변수·backend·AI service·frontend 실행 문서가 함께 영향을 받는다. |
| 최종 목표 | 팀원이 저장소 루트에서 한 가지 개발 명령으로 PostgreSQL, migration, backend, AI service, frontend, Nginx를 기동하고 `http://localhost:8080`에서 REST API·WebSocket·Hot Reload를 확인할 수 있게 한다. |
| 이번 계획 범위 | 로컬 Docker Compose 개발 실행, 서비스 간 주소/환경변수, 모델·샘플 asset 공급, seed, 통합 smoke test, 실행 문서 정합성 |
| 비목표 | 운영 배포 구조 변경, TLS/도메인, GPU/CUDA 도입, 실제 CCTV 연동, API·WebSocket 계약 변경, 새 패키지 설치 |

> 이 문서는 구현 전 조사 결과와 승인 항목을 정리한다. 루트 Compose 및 backend·AI service 파일 변경은 `frontend/AGENTS.md`의 승인 대상이므로, 아래 확인 항목을 승인받은 뒤에만 수정한다.

## 2. 현재 확인 결과

### 2.1 이미 갖춰진 통합 구조

```text
브라우저
  └─ http://localhost:8080 (Nginx)
       ├─ /                 → frontend:3000
       ├─ /api/*, /ws/*     → backend:8000
       └─ /docs (개발만)    → backend:8000

backend → ai-service:9000 → backend callback
backend → db:5432
```

- `docker-compose.yml`에는 `db`, `migrate`, `backend`, `ai-service`, `frontend`, `nginx`, opt-in `seed` profile이 정의돼 있다.
- `docker-compose.dev.yml`은 소스 bind mount, backend·AI reload, frontend `pnpm dev`, 개발 Nginx 포트 `8080`을 production Compose 위에 적용한다.
- Compose 병합 문법은 `docker compose -f docker-compose.yml -f docker-compose.dev.yml config --quiet`로 통과했다. 단, 현재 sandbox는 사용자 Docker 설정 파일을 읽을 권한이 없어 Docker CLI 경고가 출력됐으며 실제 이미지 빌드·컨테이너 기동은 아직 수행하지 않았다.
- frontend는 `next.config.mjs`에서 `COMPOSE_FRONTEND_API_BASE_URL`/`COMPOSE_FRONTEND_KAKAO_MAP_APP_KEY`를 공개 `NEXT_PUBLIC_*` 값으로 변환한다. root `.env`의 API base URL을 빈 값으로 두면 REST는 same-origin `/api/*`, WebSocket은 same-origin `/ws/drains/status`를 쓴다.
- backend와 AI service는 Compose에서 각각 `http://ai-service:9000`, `http://backend:8000`을 사용하므로 컨테이너 내부에서 `localhost`를 잘못 참조하지 않는다.

### 2.2 정비가 필요한 지점

| 항목 | 현재 상태 | 영향 |
| --- | --- | --- |
| 개발 시작 절차 | root README에는 Compose 절차가 있으나 `backend/README.md`는 과거 단독 실행·root requirements·`mock_ai_server` 경로를 안내한다. | 팀원마다 서로 다른 환경을 기동할 수 있다. |
| YOLO 모델 파일 | Compose 기본값은 `ai_service/model/best.pt`를 mount하지만 현재 저장소에는 XGBoost JSON만 있고 `best.pt`는 없다. | AI service가 실행되더라도 실제 YOLO 분석 요청은 모델 부재로 실패할 수 있다. |
| 샘플 이미지 | 개발 override의 root bind mount에서는 `/app/mock_data`를 볼 수 있지만 production AI image에는 `mock_data`를 복사하지 않는다. | 개발과 production 기준 분석 asset 구성이 달라진다. |
| 최초 실행 진단 | 모델 파일, 샘플 이미지, migration, seed 여부를 한 번에 확인하는 절차가 문서화돼 있지 않다. | 실패 원인을 서비스 로그에서만 찾아야 한다. |
| 검증 기준 | Compose config 검증 기록은 있으나 이 브랜치의 실제 컨테이너 기동·REST·WebSocket·HMR 재확인 기준이 없다. | 통합 후 회귀를 발견하기 어렵다. |

## 3. 권장 개발 환경 기준

| 구분 | 권장값 | 이유 |
| --- | --- | --- |
| 외부 진입점 | Nginx만 `localhost:8080` 공개 | 브라우저의 API/WebSocket origin을 하나로 유지하고 CORS 조건을 단순화한다. |
| frontend API URL | `COMPOSE_FRONTEND_API_BASE_URL=` (빈 값) | API 함수가 이미 `/api/*`를 포함하므로 중복 `/api/api` 없이 Nginx로 요청한다. |
| frontend WebSocket URL | 별도 `NEXT_PUBLIC_WS_URL` 미지정 | 현재 helper가 브라우저 origin에서 `ws://localhost:8080/ws/drains/status`를 만든다. |
| DB 초기화 | `migrate` 자동, `seed` 수동 profile | schema는 항상 최신화하고 개발 데이터 삽입은 사용자가 의도적으로 실행한다. |
| 코드 반영 | backend·AI `--reload`, frontend `pnpm dev` + bind mount | 저장 후 컨테이너 재빌드 없이 개발 흐름을 유지한다. |
| AI asset | host의 모델 파일을 read-only로 mount, mock image는 개발용 read-only mount 또는 명시적 image copy 중 하나로 통일 | 대용량/비공개 모델은 Git과 image에서 분리하고 샘플 데이터의 책임을 명확히 한다. |

## 4. 승인 후 구현 단계

| 단계 | 변경 내용 | 완료 기준 |
| --- | --- | --- |
| 0. 실행 기준 고정 | root `.env.example`와 README에 개발 기본 포트, same-origin URL, 모델 파일 위치, seed 정책을 한 곳에서 명시한다. 실제 `.env`의 비밀값은 읽거나 커밋하지 않는다. | 새 팀원이 필요한 입력값과 실행 명령을 알 수 있다. |
| 1. Compose 개발 설정 정비 | `docker-compose.yml`/`docker-compose.dev.yml`의 mount·environment·healthcheck·명령을 실제 backend/AI/frontend Dockerfile과 대조해 필요한 최소 변경만 적용한다. 모델 미존재 시의 동작도 선택한 정책에 맞춘다. | 모든 서비스가 올바른 내부 DNS와 개발용 source mount를 사용한다. |
| 2. AI 개발 asset 정책 반영 | 선택한 방식으로 `best.pt` 사전 검증 또는 AI 분석 비활성 개발 모드를 제공하고, mock image 경로를 명시한다. XGBoost JSON을 가리는 directory mount는 사용하지 않는다. | 모델 없는 PC에서도 기대 동작(분석 비활성 또는 명확한 사전 실패)이 일관된다. |
| 3. 문서 정합성 | root README, backend/AI/frontend 실행 문서 중 실제로 달라진 안내만 갱신한다. 특히 backend README의 과거 `mock_ai_server`·root requirements 안내를 현재 Compose 기준과 맞춘다. | Compose와 단독 실행의 목적·명령·환경변수 경계가 혼동되지 않는다. |
| 4. 통합 검증 | config, build, 기동 상태, `/`, `/api/dashboard/summary`, `/docs`, WebSocket, frontend HMR, seed, AI 분석 성공/의도적 비활성 경로를 확인한다. | 검증 결과와 실패 시 진단 명령이 step 문서에 기록된다. |

## 5. 예상 수정 범위

| 경로 | 예상 작업 | 승인 필요 |
| --- | --- | --- |
| `docker-compose.yml`, `docker-compose.dev.yml` | 개발 mount, 모델/샘플 asset 정책, 실행·검증 설정 | 예 — frontend 밖 파일 |
| `.env.example` | Compose 공개값·모델 경로 설명 정비 | 예 — frontend 밖 파일, 환경변수 변경 가능성 |
| `README.md`, `backend/README.md`, `ai_service/README.md` | 현재 개발 실행 절차와 진단 방법 정합화 | 예 — frontend 밖 파일 |
| `frontend/.env.example`, `frontend/README.md` | same-origin Compose와 단독 frontend 실행의 차이를 필요한 범위만 보완 | 환경변수 문서 변경은 예 |
| `frontend/docs/plans/*`, `steps/*`, `pr/*` | 계획·실행 결과 기록 | 현재 계획서는 작성 완료, 이후 결과에 따라 추가 |

`Dockerfile`, API route, frontend 화면 코드, 패키지/lockfile은 현재 계획의 기본 변경 대상이 아니다. Compose 검증에서 실제 원인이 확인될 때만 별도 근거와 함께 범위를 확장한다.

## 6. 검증 시나리오

1. `docker compose -f docker-compose.yml -f docker-compose.dev.yml config --quiet`로 병합 문법과 변수 치환을 확인한다.
2. 깨끗한 상태에서 `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build`를 실행하고 `db` healthy, `migrate` 성공 종료, backend·AI·frontend·nginx healthy를 확인한다.
3. 브라우저 또는 HTTP 도구로 `http://localhost:8080/`, `http://localhost:8080/api/dashboard/summary`, `http://localhost:8080/docs`를 확인한다.
4. `ws://localhost:8080/ws/drains/status` 연결을 확인한다.
5. frontend, backend, AI source를 각각 하나씩 변경해 개발 reload/HMR이 실제로 반영되는지 확인한 뒤 변경은 되돌리거나 테스트 전용 파일로 제한한다.
6. `docker compose --profile seed run --rm seed` 후 대시보드 API가 seed 데이터를 반환하는지 확인한다.
7. 모델 파일이 있는 경우 분석 요청과 callback·WebSocket 갱신을 확인한다. 모델이 없는 경우에는 선택한 정책에 따라 사전 진단 또는 분석 비활성 결과가 명확한지 확인한다.
8. `docker compose down` 후 named PostgreSQL volume이 보존되는지 확인하고, 데이터 삭제가 필요한 경우에만 `down -v`를 별도 안내한다.

## 7. 사용자 확인이 필요한 사항

| 확인 항목 | 권장안 | 선택에 따른 영향 |
| --- | --- | --- |
| AI 모델 없는 기본 개발 | **AI service는 기동하되, `best.pt`가 없으면 분석 요청만 명확하게 실패하도록 사전 진단한다.** | 대시보드·API·WebSocket 개발은 계속 가능하고, 모델 보유자는 경로만 설정해 실제 분석까지 검증할 수 있다. |
| 모델 파일 위치 | **각 개발자가 Git 외부의 절대 경로를 `.env`의 `SMARTDRAIN_YOLO_MODEL_PATH`에 지정한다.** | 대용량 모델을 저장소·Docker image에 넣지 않는다. Windows 팀 공용 경로를 정하면 예시도 함께 맞춘다. |
| 샘플 이미지 정책 | **개발 Compose에서만 `mock_data/ai_image_samples`를 read-only로 명시 mount한다.** | 개발 분석 입력을 명확히 하되, production image에는 mock 이미지를 넣지 않는다. production 분석 asset은 별도 과제로 남는다. |
| DB seed | **기본 기동에서는 자동 seed하지 않고 profile 명령을 유지한다.** | 기존 DB를 보호하며, 데모/통합 테스트 때만 의도적으로 데이터를 추가한다. |
| 외부 포트 | **Nginx 8080만 공개하고 backend·AI·DB 포트는 계속 비공개로 유지한다.** | same-origin 환경은 단순해진다. Swagger와 API는 Nginx 경유 주소를 사용한다. |

## 8. 리스크와 대응

| 리스크 | 대응 |
| --- | --- |
| `best.pt` 누락을 컨테이너 기동 후에야 발견 | 기동 전 파일 존재·일반 파일 여부를 검사하고, 모델이 없는 기본 개발 정책을 문서화한다. |
| host 경로 차이(Windows/WSL/Docker Desktop) | `.env`에는 절대 경로 예시와 OS별 확인 명령을 제공하고, 경로를 Compose 파일에 하드코딩하지 않는다. |
| bind mount가 image 내부 결과물을 가림 | 개발 override에 필요한 source/asset만 좁게 mount하고 node_modules와 XGBoost artifact 경로를 별도 점검한다. |
| seed 반복으로 데이터가 오염 | 기존 opt-in profile과 idempotent seed 동작을 유지하고, 초기화 명령은 위험성을 문서에 명시한다. |
| 문서와 실행 설정이 다시 어긋남 | Compose 변경과 같은 PR에서 root README 및 서비스 README의 해당 명령을 함께 갱신하고, step 문서에 실제 검증 명령을 남긴다. |

## 9. 승인 후 첫 작업

사용자가 7절의 AI asset·seed·포트 정책을 승인하면, 우선 모델 파일 사전 진단 방식과 개발용 mock image read-only mount를 확정한다. 이후 Compose 변경을 작은 단위로 적용하고 실제 Docker 기동 결과를 확인한 뒤 `frontend/docs/steps/step-22-...md`에 결과·남은 리스크를 기록한다.
