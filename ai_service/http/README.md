# AI Service HTTP Layer

`ai_service/http` contains the FastAPI adapter for the SmartDrain AI service.

## Endpoint

`POST /ai/analysis/run`

The endpoint accepts the backend analysis request payload, validates it, creates the deterministic MVP job ID, schedules background callback processing, and immediately returns:

{
    "accepted": true,
    "request_id": "REQ_20260618_001",
    "job_id": "AI_JOB_REQ_20260618_001",
    "status": "processing"
}

The endpoint is a thin adapter around the existing analysis layer. It does not run real YOLO, call CCTV APIs, touch the database, or modify the XGBoost contract.

## Background Callback Flow

Background processing:

1. Run `run_analysis_job(payload)`.
2. Send YOLO callback payload to `/api/ai-callback/yolo-result`.
3. Send XGBoost callback payload to `/api/ai-callback/xgboost-result`.

Callback delivery is best-effort for MVP:

- callback success or failure does not change the accepted response
- XGBoost callback is attempted even if YOLO callback fails
- each callback uses timeout
- each callback retries at most once by default
- no persistent retry queue is implemented

## Configuration

Environment variables:

- `BACKEND_BASE_URL`, default `http://localhost:8000`
- `BACKEND_CALLBACK_TIMEOUT_SECONDS`, default `10`
- `BACKEND_CALLBACK_RETRY_COUNT`, default `1`

AI server local port:

- `9000`

Run command:

python -m uvicorn ai_service.http.app:app --host 0.0.0.0 --port 9000 --reload

