# SmartDrain Backend

SmartDrain backend는 FastAPI 기반 API 서버입니다. 시설/센서/분석 결과를 PostgreSQL에 저장하고, AI Service callback을 받아 WebSocket으로 frontend에 상태 변경을 전달합니다.

## 책임 범위

- REST API: 시설, 센서, 대시보드, 분석 이력 조회
- WebSocket: `/ws/drains/status` 실시간 이벤트 발행
- DB schema: SQLAlchemy model과 Alembic migration 관리
- AI 연동: 분석 job 생성, AI Service 요청, YOLO/XGBoost callback 저장
- Seed: 로컬/시연용 mock drain 데이터 생성

## 디렉터리 구조

```text
backend/
├─ app/
│  ├─ core/          # 설정과 DB 연결
│  ├─ models/        # SQLAlchemy 모델
│  ├─ routers/       # REST, callback, websocket endpoint
│  ├─ schemas/       # Pydantic schema와 API response
│  ├─ services/      # 도메인 로직과 AI 연동 로직
│  ├─ seeds/         # mock data seed
│  └─ websocket/     # WebSocket connection manager
├─ alembic/          # migration scripts
├─ alembic.ini       # backend 전용 Alembic 설정
├─ requirements.txt  # backend runtime 의존성
├─ Dockerfile
└─ README.md
```

## 로컬 단독 실행

전체 통합 실행은 루트 README의 Docker Compose 절차를 권장합니다. backend만 단독으로 수정하거나 디버깅할 때는 아래 순서를 사용합니다.

### 1. backend 폴더로 이동

```powershell
cd C:\Dev\smartdrain-agent-upgrade\backend
```

### 2. Python 가상환경 생성 및 활성화

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. 의존성 설치

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. 환경변수 준비

```powershell
Copy-Item .env.example .env
```

기본 로컬 DB URL은 `backend/.env.example`에 정의되어 있습니다. Docker Compose의 PostgreSQL을 함께 사용할 수 있습니다.

### 5. PostgreSQL 실행

프로젝트 루트에서 DB를 포함한 Compose를 실행하거나, 로컬 PostgreSQL을 직접 준비합니다.

```powershell
cd C:\Dev\smartdrain-agent-upgrade
docker compose up -d db
```

### 6. Alembic migration 실행

`alembic.ini`는 `backend/` 안에 있으므로 backend 디렉터리에서 실행합니다.

```powershell
cd C:\Dev\smartdrain-agent-upgrade\backend
python -m alembic upgrade head
```

### 7. mock seed 데이터 삽입

```powershell
python -m app.seeds.seed_mock_data
```

생성되는 기본 시설:

- `DR-001`: `good`
- `DR-002`: `good`
- `DR-003`: `caution`
- `DR-004`: `danger`
- `DR-005`: `unknown`

이미 같은 `drain_code`가 있으면 중복 생성하지 않고 건너뜁니다.

### 8. FastAPI 서버 실행

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

Swagger:

```text
http://localhost:8000/docs
```

## AI Service 연동

`POST /api/analysis/async-run`은 backend가 AI Service로 분석 요청을 보내는 API입니다. 이 API가 정상 동작하려면 실제 AI Service 또는 mock AI 서버가 `9000`번 포트에서 실행 중이어야 합니다.

실제 AI Service 실행은 루트에서 다음 명령을 사용합니다.

```powershell
python -m uvicorn ai_service.http.app:app --host 0.0.0.0 --port 9000 --reload
```

개발용 mock AI 서버를 사용할 수도 있습니다.

```powershell
python -m uvicorn mock_ai_server.main:app --reload --port 9000
```

## Backend-AI Async Analysis

사용 endpoint:

- Backend -> AI: `POST {AI_SERVER_BASE_URL}/ai/analysis/run`
- AI -> Backend: `POST /api/ai-callback/yolo-result`
- AI -> Backend: `POST /api/ai-callback/xgboost-result`
- Backend 내부 실행 API: `POST /api/analysis/async-run`

주요 환경변수:

```env
AI_SERVER_BASE_URL=http://localhost:9000
AI_SERVER_TIMEOUT_SECONDS=10
AI_CALLBACK_BASE_URL=http://localhost:8000
AI_SERVER_ENABLED=true
ANALYSIS_SCHEDULER_ENABLED=false
ANALYSIS_SCHEDULER_INTERVAL_SECONDS=300
ANALYSIS_SCHEDULER_INITIAL_DELAY_SECONDS=60
ANALYSIS_SENSOR_MAX_AGE_SECONDS=300
ANALYSIS_JOB_TIMEOUT_SECONDS=600
```

### AnalysisJob 저장 정책

- `/api/analysis/async-run`은 AI 서버 호출 전에 `analysis_jobs` row를 먼저 생성합니다.
- `request_id`는 backend가 생성합니다.
- `job_id`는 `AI_JOB_{request_id}` 형식으로 backend가 먼저 생성하고, AI 서버 요청에도 같은 값을 전달합니다.
- 수동 분석은 `trigger_type=manual`, scheduler 분석은 `trigger_type=scheduled`로 저장합니다.
- AI 서버 호출 실패, timeout, 4xx/5xx 응답이 발생하면 이미 생성된 job을 `status=failed`로 변경하고 `error_message`에 실패 원인을 저장합니다.

### Callback 멱등성

- YOLO callback은 같은 `request_id`/`job_id`에 이미 `yolo_result_id`가 있으면 새 `YoloResult`를 만들지 않고 200 OK로 응답합니다.
- XGBoost callback은 같은 `request_id`/`job_id`가 이미 `completed`이고 연결된 결과가 있으면 새 `XgboostResult`를 만들지 않고 200 OK로 응답합니다.
- 중복 callback에서는 WebSocket 이벤트를 재발행하지 않습니다.

### Scheduler

- 기본값은 `ANALYSIS_SCHEDULER_ENABLED=false`이며, 이 상태에서는 서버 시작 시 자동 분석 요청이 나가지 않습니다.
- `true`로 설정하면 startup 후 `ANALYSIS_SCHEDULER_INITIAL_DELAY_SECONDS`만큼 기다린 뒤 주기적으로 실행됩니다.
- scheduler는 최신 센서 데이터가 없거나, 같은 drain에 진행 중 job이 있거나, 마지막 job 생성 시각이 주기 이내이면 skip합니다.
- timeout을 초과한 `processing`/`yolo_completed` job은 `failed`로 변경합니다.

### Realtime Simulator (런타임 자동 모드)

- 수동 `POST /api/analysis/async-run` 방식은 그대로 유지합니다.
- 별도 런타임 제어 API로 자동 시뮬레이션을 시작/중지할 수 있습니다.
- 자동 모드는 주기적으로 센서 데이터를 생성하고, drain별 비동기 분석 요청을 실행합니다.
- 자동 모드 분석 요청의 `analysis_jobs.trigger_type`은 `scheduled`로 저장됩니다.

시뮬레이터 제어 API:

- `GET /api/realtime-simulator/status`
- `POST /api/realtime-simulator/start`
- `POST /api/realtime-simulator/stop`

## 주요 API 확인

- `GET /api/drains`
- `GET /api/dashboard/summary`
- `GET /api/drains/DR-004`
- `GET /api/drains/DR-004/sensor-data`
- `GET /api/drains/DR-004/risk-history`
- `GET /api/drains/DR-004/analysis/latest`
- `POST /api/analysis/async-run`
- `GET /api/realtime-simulator/status`
- `POST /api/realtime-simulator/start`
- `POST /api/realtime-simulator/stop`

분석 시작 요청 예시:

```powershell
$base = "http://localhost:8000"
Invoke-RestMethod -Method Post -Uri "$base/api/analysis/async-run" -ContentType "application/json" -Body '{
  "drainId": "DR-004"
}'
```

## WebSocket 이벤트

프론트엔드는 단일 WebSocket endpoint인 `/ws/drains/status`에 연결하고, 메시지의 `type` 값으로 이벤트를 구분합니다.

지원 이벤트:

- `YOLO_RESULT_UPDATED`: YOLO 중간 분석 결과 저장 후 발행
- `XGBOOST_RESULT_UPDATED`: XGBoost 최종 분석 결과 저장 후 발행
- `DRAIN_STATUS_UPDATED`: 대시보드/상세 화면 갱신용 최종 상태 요약 발행

WebSocket 확인 예시:

```js
const socket = new WebSocket("ws://localhost:8000/ws/drains/status");
socket.onopen = () => console.log("ws connected");
socket.onmessage = (event) => console.log(JSON.parse(event.data));
```

## 검증

```powershell
cd C:\Dev\smartdrain-agent-upgrade\backend
python -m compileall app
python -m alembic upgrade head
```

통합 흐름은 루트에서 Docker Compose로 확인합니다.

```powershell
cd C:\Dev\smartdrain-agent-upgrade
docker compose -f docker-compose.yml -f docker-compose.dev.yml config --quiet
```
