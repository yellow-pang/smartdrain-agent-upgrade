# SmartDrain Backend

## Backend 실행 방법

처음 실행하는 팀원은 아래 순서대로 진행합니다. Windows PowerShell 기준 명령어입니다.

### 1. backend 폴더로 이동

```bash
cd C:\AI_agent\LMG_WORK2026\smartdrain\backend
```

### 2. Python 가상환경 생성

```bash
python -m venv .venv
```

### 3. 가상환경 활성화

```bash
.venv\Scripts\activate
```

### 4. requirements 설치

`requirements.txt`는 프로젝트 루트에 있습니다.

```bash
pip install -r ..\requirements.txt
```

### 5. PostgreSQL Docker 실행 확인

프로젝트 루트에서 Docker Compose를 실행합니다.

```bash
cd C:\AI_agent\LMG_WORK2026\smartdrain
docker compose up -d
```

### 6. Alembic 마이그레이션 실행

`alembic.ini`가 프로젝트 루트에 있으므로 루트에서 실행합니다.

```bash
python -m alembic upgrade head
```

### 7. mock seed 데이터 삽입

seed 스크립트는 `backend` 폴더 기준으로 실행합니다.

```bash
cd C:\AI_agent\LMG_WORK2026\smartdrain\backend
python -m app.seeds.seed_mock_data
```

### 8. FastAPI 백엔드 서버 실행

```bash
uvicorn app.main:app --reload --port 8000
```

### 9. Swagger 접속 확인

```txt
http://localhost:8000/docs
```

## AI 서버 실행 안내

`POST /api/analysis/async-run`은 백엔드가 AI 서버로 분석 요청을 보내는 API입니다. 이 API가 정상 동작하려면 실제 AI 서버 또는 mock AI 서버가 `9000`번 포트에서 실행 중이어야 합니다.

```bash
cd C:\AI_agent\LMG_WORK2026\smartdrain
uvicorn mock_ai_server.main:app --reload --port 9000
```

환경변수 예시는 아래 Backend-AI Async Analysis 섹션의 값을 사용합니다.

## Seed Mock Data

프론트-백엔드 연동 테스트 전에 PostgreSQL DB에 대시보드와 상세 화면 확인용 목 데이터를 넣기 위한 seed 스크립트입니다.

생성되는 데이터:

- `DR-001`: `good`
- `DR-002`: `good`
- `DR-003`: `caution`
- `DR-004`: `danger`
- `DR-005`: `unknown`

각 빗물받이에 대해 `sensor_data`, `yolo_result`, `xgboost_result`가 함께 생성됩니다. 이미 같은 `drain_code`가 있으면 중복 생성하지 않고 건너뜁니다.

## 실행 명령어

DB 테이블은 먼저 Alembic 마이그레이션으로 생성되어 있어야 합니다. 전체 실행 순서는 위의 Backend 실행 방법을 참고합니다.

`backend` 폴더 기준:

```bash
python -m app.seeds.seed_mock_data
```

## 실행 후 확인할 API

- `GET /api/drains`
- `GET /api/dashboard/summary`
- `GET /api/drains/DR-004`
- `GET /api/drains/DR-004/sensors`
- `GET /api/drains/DR-004/risk-history`
- `GET /api/drains/DR-004/analysis/latest`

## Backend-AI Async Analysis

백엔드는 최신 센서 데이터를 AI 서버로 보내 분석 job을 시작하고, AI 서버가 callback으로 전달하는 YOLO 중간 결과와 XGBoost 최종 결과를 DB에 저장합니다. callback 저장 후에는 `/ws/drains/status` WebSocket으로 프론트에 이벤트를 발행합니다.

사용 endpoint:

- Backend -> AI: `POST {AI_SERVER_BASE_URL}/ai/analysis/run`
- AI -> Backend: `POST /api/ai-callback/yolo-result`
- AI -> Backend: `POST /api/ai-callback/xgboost-result`
- Backend 내부 실행 API: `POST /api/analysis/async-run`

환경변수:

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
- `request_id`는 백엔드가 생성합니다.
- `job_id`는 `AI_JOB_{request_id}` 형식으로 백엔드가 먼저 생성하고, AI 서버 요청에도 같은 값을 전달합니다.
- 수동 분석은 `trigger_type=manual`, scheduler 분석은 `trigger_type=scheduled`로 저장합니다.
- AI 서버 호출 실패, timeout, 4xx/5xx 응답이 발생하면 이미 생성된 job을 `status=failed`로 변경하고 `error_message`에 실패 원인을 저장합니다.

### Callback 멱등성

- YOLO callback은 같은 `request_id`/`job_id`에 이미 `yolo_result_id`가 있으면 새 `YoloResult`를 만들지 않고 200 OK로 응답합니다.
- XGBoost callback은 같은 `request_id`/`job_id`가 이미 `completed`이고 연결된 결과가 있으면 새 `XgboostResult`를 만들지 않고 200 OK로 응답합니다.
- 중복 callback에서는 WebSocket 이벤트를 재발행하지 않습니다.

### Scheduler

- 기본값은 `ANALYSIS_SCHEDULER_ENABLED=false`이며, 이 상태에서는 서버 시작 시 자동 분석 요청이 나가지 않습니다.
- `true`로 설정하면 startup 후 `ANALYSIS_SCHEDULER_INITIAL_DELAY_SECONDS`만큼 기다린 뒤 주기적으로 실행됩니다.
- scheduler는 모든 drain을 순회하며 최신 센서 데이터가 없거나, 센서 데이터가 `ANALYSIS_SENSOR_MAX_AGE_SECONDS`보다 오래됐거나, 같은 drain에 `processing`/`yolo_completed` job이 있거나, 마지막 job 생성 시각이 `ANALYSIS_SCHEDULER_INTERVAL_SECONDS` 이내이면 skip합니다.
- 조건을 통과한 drain만 `trigger_type=scheduled` job으로 생성하고 AI 서버에 분석을 요청합니다.
- scheduler 실행 시 `processing`/`yolo_completed` 상태가 `ANALYSIS_JOB_TIMEOUT_SECONDS`를 초과한 job은 `failed`로 변경합니다.

### Smoke Test

1. `ANALYSIS_SCHEDULER_ENABLED=false` 상태로 백엔드를 실행해 자동 분석 요청이 발생하지 않는지 확인합니다.
2. AI 서버를 끄고 `POST /api/analysis/async-run`을 호출해 `analysis_jobs.status=failed`와 `error_message`가 남는지 확인합니다.
3. mock AI 서버를 켜고 `POST /api/analysis/async-run`을 호출해 정상 accepted 응답과 callback 저장을 확인합니다.
4. 같은 YOLO callback을 2번 호출해 `yolo_results`가 중복 생성되지 않는지 확인합니다.
5. 같은 XGBoost callback을 2번 호출해 `xgboost_results`가 중복 생성되지 않는지 확인합니다.
6. `ANALYSIS_SCHEDULER_ENABLED=true`로 켠 뒤 initial delay 이후 조건을 만족하는 drain에만 scheduled job이 생성되는지 확인합니다.
7. `GET /api/drains`, `GET /api/drains/{id}`, `POST /api/drains` 응답에서 `roadAddress`, `fullAddress`, `finalDecision` 등 한글 문자열이 깨지지 않고 UTF-8 JSON으로 내려오는지 확인합니다.

분석 시작 요청 예시:

```powershell
$base = "http://localhost:8000"
Invoke-RestMethod -Method Post -Uri "$base/api/analysis/async-run" -ContentType "application/json" -Body '{
  "drainId": "DR-004"
}'
```

AI 서버가 없으면 `ANALYSIS_UNAVAILABLE` 에러 wrapper가 반환됩니다.

YOLO callback 테스트 예시:

```powershell
Invoke-RestMethod -Method Post -Uri "$base/api/ai-callback/yolo-result" -ContentType "application/json" -Body '{
  "request_id": "REQ_202606190001_4",
  "job_id": "AI_JOB_001",
  "yolo_result": {
    "obstruction_ratio": 0.82,
    "confidence_score": 0.94,
    "yolo_status": "blocked"
  }
}'
```

XGBoost callback 테스트 예시:

```powershell
Invoke-RestMethod -Method Post -Uri "$base/api/ai-callback/xgboost-result" -ContentType "application/json" -Body '{
  "request_id": "REQ_202606190001_4",
  "job_id": "AI_JOB_001",
  "xgboost_result": {
    "risk_score": 0.91,
    "risk_level": "danger",
    "final_decision": "dispatch_required",
    "evaluated_at": "2026-06-18T08:36:25+09:00"
  }
}'
```

WebSocket 이벤트 확인:

```js
const socket = new WebSocket("ws://localhost:8000/ws/drains/status");
socket.onopen = () => console.log("ws connected");
socket.onmessage = (event) => console.log(JSON.parse(event.data));
```

WebSocket 이벤트 타입:

- `YOLO_RESULT_UPDATED`: YOLO 중간 결과 저장 후 전달
- `XGBOOST_RESULT_UPDATED`: XGBoost 최종 분석 결과 저장 후 전달
- `DRAIN_STATUS_UPDATED`: 대시보드/상세 화면 갱신용 최종 상태 요약 전달

두 이벤트는 모두 `/ws/drains/status`로 전달되며, 프론트는 `type` 기준으로 분기 처리합니다.

`YOLO_RESULT_UPDATED` 예시:

```json
{
  "type": "YOLO_RESULT_UPDATED",
  "payload": {
    "drainId": "DR-004",
    "yoloResultId": 8,
    "imageUrl": "/test-snapshots/drain-001-b.jpg",
    "obstructionRatio": 0.82,
    "confidenceScore": 0.94,
    "yoloStatus": "blocked",
    "capturedAt": "2026-06-19T12:42:00+09:00",
    "analyzedAt": "2026-06-19T12:42:01+09:00",
    "updatedAt": "2026-06-19T12:42:01+09:00"
  }
}
```

`DRAIN_STATUS_UPDATED` 예시:

```json
{
  "type": "DRAIN_STATUS_UPDATED",
  "payload": {
    "drainId": "DR-004",
    "requestId": "REQ_202606190001_4",
    "jobId": "AI_JOB_001",
    "riskLevel": "danger",
    "riskScore": 0.91,
    "waterLevelCm": 85,
    "flowVelocityMps": 0.05,
    "obstructionRatio": 0.82,
    "confidenceScore": 0.94,
    "yoloStatus": "blocked",
    "finalDecision": "dispatch_required",
    "updatedAt": "2026-06-18T08:36:25+09:00"
  }
}
```

주의:

- callback 테스트에는 먼저 `/api/analysis/async-run`으로 생성된 실제 `requestId`, `jobId`를 사용합니다.
- Backend -> AI 요청 body에는 이미지 URL, snapshot URL, CCTV URL을 포함하지 않습니다.
- AI 서버는 `drain_id` 기준으로 내부 mock image를 사용한다고 가정합니다.

## Frontend WebSocket / Analysis History Contract

프론트엔드는 단일 WebSocket endpoint인 `/ws/drains/status`에 연결하고, 수신한 메시지의 `type` 값으로 이벤트를 구분합니다.

### Drain 목록 이미지 필드

`GET /api/drains`의 각 item에는 기존 필드에 더해 최신 YOLO 이미지 정보가 optional 필드로 포함됩니다.

- `latestImageUrl`: 해당 drain의 가장 최근 YOLO 분석 이미지 URL입니다. 이미지가 없으면 `null`입니다.
- `latestImageCapturedAt`: 해당 이미지의 `capturedAt` ISO 8601 문자열입니다. 이미지가 없으면 `null`입니다.

최신 YOLO 결과는 `capturedAt` 기준으로 판단하고, `capturedAt`이 없거나 같은 경우 `createdAt`을 보조 기준으로 사용합니다.

프론트는 목록/선택 시설 패널의 초기 이미지에 `latestImageUrl`을 사용하고, 실시간 갱신은 `YOLO_RESULT_UPDATED.payload.imageUrl`을 사용합니다.

지원 이벤트:

- `YOLO_RESULT_UPDATED`: YOLO 중간 분석 결과 저장 후 발행
- `XGBOOST_RESULT_UPDATED`: XGBoost 최종 분석 결과 저장 후 발행
- `DRAIN_STATUS_UPDATED`: 대시보드/상세 화면 갱신용 최종 상태 요약 발행

`YOLO_RESULT_UPDATED` payload:

```json
{
  "drainId": "DR-004",
  "yoloResultId": 1,
  "imageUrl": "ai-server://mock/4",
  "obstructionRatio": 0.82,
  "confidenceScore": 0.94,
  "yoloStatus": "blocked",
  "capturedAt": "2026-06-18T08:36:20+09:00",
  "analyzedAt": "2026-06-18T08:36:20+09:00",
  "updatedAt": "2026-06-18T08:36:20+09:00"
}
```

`XGBOOST_RESULT_UPDATED` payload:

```json
{
  "drainId": "DR-004",
  "xgboostResultId": 1,
  "sensorDataId": 1,
  "yoloResultId": 1,
  "riskLevel": "danger",
  "riskScore": 0.91,
  "finalDecision": "dispatch_required",
  "evaluatedAt": "2026-06-18T08:36:25+09:00",
  "updatedAt": "2026-06-18T08:36:25+09:00"
}
```

`DRAIN_STATUS_UPDATED` payload:

```json
{
  "drainId": "DR-004",
  "riskLevel": "danger",
  "riskScore": 0.91,
  "waterLevelCm": 85,
  "flowVelocityMps": 0.05,
  "obstructionRatio": 0.82,
  "finalDecision": "dispatch_required",
  "updatedAt": "2026-06-18T08:36:25+09:00",
  "sensorDataId": 1,
  "yoloResultId": 1,
  "xgboostResultId": 1
}
```

### XGBoost / Drain Status 연결 기준

- `XGBOOST_RESULT_UPDATED.payload.yoloResultId`는 XGBoost 결과가 실제 저장될 때 연결된 `xgboost_results.yolo_result_id`입니다.
- `DRAIN_STATUS_UPDATED.payload.yoloResultId`도 같은 XGBoost 결과에 연결된 YOLO 결과 ID입니다.
- `DRAIN_STATUS_UPDATED.payload.obstructionRatio`는 최신 YOLO 결과가 아니라, 해당 XGBoost 결과의 `yoloResultId`로 연결된 YOLO 결과의 `obstructionRatio`입니다.
- `POST /api/drains` 응답은 기존 `id` 필드 값을 유지하며, 내부 숫자 PK는 하위 호환 optional 필드인 `internalId`로 함께 내려갑니다.

분석 이력은 WebSocket이 아니라 REST API로 조회합니다.

- `GET /api/drains/{drain_id}/analysis/yolo?limit=10`
- `GET /api/drains/{drain_id}/analysis/xgboost?limit=10`
- `GET /api/drains/{drain_id}/analysis/history?limit=10`
