# AI Server HTTP API Design

This document describes how the current internal AI service orchestration should connect to a future HTTP API layer.

No FastAPI, Flask, callback sender, database access, WebSocket, or server runtime code is implemented in this stage.

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
