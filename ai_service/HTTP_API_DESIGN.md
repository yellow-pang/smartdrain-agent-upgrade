# AI Server HTTP API Design

This document describes how the current internal AI service orchestration should connect to a future HTTP API layer.

No FastAPI, Flask, callback sender, database access, WebSocket, or server runtime code is implemented in this stage.

## Layer Responsibility Rule

Backend communication must be isolated to the future `ai_service/http` layer.

- `http`: HTTP endpoint, background tasks, callback sender, timeout, retry, logging, and HTTP error mapping.
- `analysis`: orchestration and callback-ready payload dictionary assembly only.
- `_yolo`: predictor-only module that returns YOLO result values.
- `xgboost`: predictor-only module that returns risk result values.

`_yolo`, `xgboost`, and `analysis` must not send callbacks or know backend URLs.

## Contract Basis

The current AI service direction follows the asynchronous backend-AI analysis API document:

- `POST /ai/analysis/run`
- `POST /api/ai-callback/yolo-result`
- `POST /api/ai-callback/xgboost-result`

The sensor-only synchronous endpoint shape such as `/ai/xgboost/predict` is not the current contract basis for this package.

The backend sends latest sensor values only. It does not send image paths, snapshot URLs, or CCTV URLs. The AI server owns image-source selection by `drain_id`; in the current MVP code this is represented by deterministic fake YOLO results.

## Framework Status

The AI server HTTP framework is not selected in this repository yet.

Because no framework dependency or server entrypoint exists, this stage keeps the HTTP layer as a design contract only.

When the framework is selected, the HTTP endpoint should be a thin adapter around the existing analysis orchestration function.

## Stage 5 Decision

Endpoint skeleton implementation is deferred.

Reason:

- No server framework dependency is present.
- No existing AI server app entrypoint is present.
- Adding FastAPI or Flask now would create a framework decision before the team has selected one.

Therefore this repository currently keeps HTTP behavior as a design contract and does not add `ai_service/http/` runtime code yet.

The next implementation step should start only after the team confirms the framework and dependency management approach.

## Latest Repository Check

The repository was checked for framework indicators before adding endpoint code.

No server framework or dependency-management standard is currently present:

- No FastAPI, Flask, Django, Starlette, aiohttp, uvicorn, or gunicorn usage was found.
- No requirements, pyproject, setup, Pipfile, poetry, uv, conda, or environment file was found at the repository root.
- No AI server HTTP entrypoint exists yet.

Decision:

- Do not create `ai_service/http/` yet.
- Do not add framework dependencies.
- Keep `run_analysis_job(payload)` as the stable internal integration point.
- Revisit endpoint implementation after the team confirms the server framework.

## Target Endpoints

Backend to AI server:

- Method: `POST`
- Path: `/ai/analysis/run`
- Purpose: request analysis for one drain using latest sensor data.

AI server to Backend callbacks:

- Method: `POST`
- Path: `/api/ai-callback/yolo-result`
- Purpose: send YOLO intermediate result.

- Method: `POST`
- Path: `/api/ai-callback/xgboost-result`
- Purpose: send XGBoost final result.

## Current Internal Entrypoint

The current internal entrypoint is:

`ai_service.analysis.service.run_analysis_job(payload)`

Import example:

`from ai_service.analysis.service import run_analysis_job`

The future `/ai/analysis/run` endpoint should call this function after parsing the request body.

## Job ID Policy

The current MVP job ID is deterministic:

`job_id = AI_JOB_{request_id}`

Example:

- `request_id = REQ_20260618_001`
- `job_id = AI_JOB_REQ_20260618_001`

This is an internal MVP policy. It can be replaced later with a UUID, sequence, database job table, or queue-generated job ID when the server runtime exists.

## Request Body

The future `/ai/analysis/run` request body should match the current analysis payload:

{
    "request_id": "REQ_20260618_001",
    "drain_id": 2,
    "sensor_data": {
        "measured_at": "2026-06-18T08:36:13+09:00",
        "water_level_cm": 98.13,
        "flow_velocity_mps": 0.4512,
        "quality_status": "valid"
    }
}

## Internal Result

`run_analysis_job(payload)` returns:

{
    "accepted_response": {...},
    "yolo_callback_payload": {...},
    "xgboost_callback_payload": {...}
}

`yolo_callback_payload` and `xgboost_callback_payload` are callback-ready dictionaries. They are not sent over HTTP by the current implementation.

## Callback Payload Contracts

YOLO callback payload:

- `request_id`
- `job_id`
- `yolo_result.obstruction_ratio`
- `yolo_result.confidence_score`
- `yolo_result.yolo_status`

Allowed `yolo_status` values:

- `good`
- `dirty`
- `blocked`
- `unknown`

The source API document lists `good`, `dirty`, and `blocked` for MVP. This project additionally allows `unknown` for fallback or status-unavailable cases.

XGBoost callback payload:

- `request_id`
- `job_id`
- `xgboost_result.risk_score`
- `xgboost_result.risk_level`
- `xgboost_result.final_decision`
- `xgboost_result.evaluated_at`

Allowed `risk_level` values:

- `good`
- `caution`
- `danger`
- `unknown`

Allowed backend `final_decision` values:

- `normal`
- `monitoring`
- `field_check`
- `dispatch_required`

## Future Endpoint Adapter Shape

The future HTTP endpoint should only adapt HTTP input/output around the orchestration layer.

Expected flow:

1. Receive JSON body from `POST /ai/analysis/run`.
2. Pass the parsed body to `run_analysis_job(payload)`.
3. Return `accepted_response` immediately.
4. Send `yolo_callback_payload` to the backend callback endpoint later.
5. Send `xgboost_callback_payload` to the backend callback endpoint later.

Current implementation stops at step 3 as an internal dictionary result. It does not send callbacks.

## Callback Sender Boundary

The current analysis package builds callback payload dictionaries only.

It does not:

- open network connections
- retry failed callbacks
- store pending jobs
- persist callback status
- map HTTP status codes

Those concerns belong to a future HTTP/callback sender layer.

## Callback Sender Design Draft

If the server framework is still not selected, implement no callback sender runtime code.

When the HTTP layer is added, callback sender behavior should follow the MVP best-effort policy:

- `POST /ai/analysis/run` returns `accepted_response` after request validation and job acceptance.
- Callback success or failure must not change the already-returned accepted response.
- Send YOLO callback first.
- Send XGBoost callback after YOLO callback is attempted.
- If YOLO callback fails, still attempt XGBoost callback.
- Use a timeout for each callback request.
- Retry each callback at most once.
- If retry fails, log and drop the callback.
- Do not implement a persistent retry queue in MVP.
- Do not store callback state in a database in this package.

## Error Boundary

The current analysis layer raises `ValueError` for invalid payloads.

The future HTTP layer should translate `ValueError` into an appropriate client error response, likely HTTP `400 Bad Request`.

The exact error response body should be agreed with the backend before implementation.

## Recommended File Placement Later

If the team selects FastAPI or Flask later, keep framework-specific code separate from pure analysis logic.

Suggested future shape:

ai_service/
├─ analysis/
│  └─ service.py
├─ http/
│  ├─ app.py
│  ├─ routes.py
│  └─ callback_sender.py
└─ HTTP_API_DESIGN.md

`analysis` should remain importable and testable without network, DB, or server dependencies.

## Framework Selection Checklist

Before implementing endpoint code, decide:

- HTTP framework: FastAPI, Flask, or another server framework.
- Dependency management: requirements file, pyproject, uv, poetry, or existing team standard.
- Server entrypoint location.
- Runtime command for local development.
- Error response shape for `ValueError`.
- Whether `/ai/analysis/run` should run callbacks synchronously in MVP or enqueue background work.
- Callback sender retry and failure policy.

Until these are decided, `run_analysis_job(payload)` remains the stable internal integration point.
