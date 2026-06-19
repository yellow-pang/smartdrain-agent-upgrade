# SmartDrain Backend

## Seed Mock Data

프론트-백엔드 연동 테스트 전에 PostgreSQL DB에 대시보드와 상세 화면 확인용 목 데이터를 넣기 위한 seed 스크립트입니다.

생성되는 데이터:

- `DR-001`: `good`
- `DR-002`: `good`
- `DR-003`: `caution`
- `DR-004`: `danger`
- `DR-005`: `unknown`

각 빗물받이에 대해 `sensor_data`, `yolo_result`, `xgboost_result`가 함께 생성됩니다. 이미 같은 `drain_code`가 있으면 중복 생성하지 않고 건너뜁니다.

## 실행 전 준비

DB 테이블은 Alembic 마이그레이션으로 먼저 생성되어 있어야 합니다.

프로젝트 루트에서:

```bash
python -m alembic upgrade head
```

## 실행 명령어

프로젝트 루트에서:

```bash
cd backend
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
```

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
- `DRAIN_STATUS_UPDATED`: XGBoost 최종 위험도 결과 저장 후 전달

두 이벤트는 모두 `/ws/drains/status`로 전달되며, 프론트는 `type` 기준으로 분기 처리합니다.

`YOLO_RESULT_UPDATED` 예시:

```json
{
  "type": "YOLO_RESULT_UPDATED",
  "payload": {
    "drainId": "DR-004",
    "requestId": "REQ_202606190001_4",
    "jobId": "AI_JOB_001",
    "obstructionRatio": 0.82,
    "confidenceScore": 0.94,
    "yoloStatus": "blocked",
    "updatedAt": "2026-06-18T08:36:20+09:00"
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
