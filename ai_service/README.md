# SmartDrain AI Service

This directory contains the SmartDrain AI server area.

The current implementation provides analysis orchestration, a fake YOLO stub, the XGBoost inference contract, and a temporary rule-based XGBoost baseline predictor. It does not contain real YOLO execution or a trained XGBoost model.

The internal analysis flow can now build accepted responses, YOLO callback payloads, and XGBoost callback payloads without HTTP endpoints or real callback sending.

## Planned Flow

The backend-AI server integration will follow this asynchronous shape:

- `POST /ai/analysis/run`
- `POST /api/ai-callback/yolo-result`
- `POST /api/ai-callback/xgboost-result`

This asynchronous contract is the current basis for `ai_service`. A sensor-only synchronous endpoint such as `/ai/xgboost/predict` is not the current target for this package.

The AI service will receive the latest sensor values from the backend, resolve the image source internally by `drain_id`, run YOLO, run XGBoost with YOLO and sensor features, and build callback payloads.

The HTTP API layer is not implemented yet. The current HTTP connection design is documented in `ai_service/HTTP_API_DESIGN.md`.

The endpoint skeleton is intentionally deferred until the team selects a server framework and dependency management approach.
The repository currently has no server framework dependency or AI server HTTP entrypoint.

## Current Limits

The following are not implemented yet:

- Real YOLO execution.
- CCTV API calls.
- Image processing.
- Database reads or writes.
- HTTP callback sending.
- FastAPI or Flask endpoints.
- Real XGBoost model loading or training.

Currently implemented:

- fake YOLO for MVP drain IDs
- rule-based XGBoost baseline
- internal analysis orchestration
- accepted response payload creation
- YOLO callback payload creation
- XGBoost callback payload creation

## Current Fake YOLO

`ai_service/_yolo` contains deterministic mock YOLO results for MVP drain IDs `1`, `2`, `3`, and `4`. These values were copied from sample YOLO JSON output and fixed in code. The fake predictor does not read images, call CCTV APIs, load a YOLO model, or read the external sample JSON at runtime.

Allowed YOLO statuses are `good`, `dirty`, `blocked`, and `unknown`. The asynchronous API source document lists `good`, `dirty`, and `blocked`; this project additionally allows `unknown` for fallback or status-unavailable cases.

## Current Analysis Orchestration

`ai_service/analysis` accepts the backend analysis request shape, validates it, creates a deterministic job ID, calls fake YOLO, converts YOLO and sensor values into the XGBoost input contract, runs XGBoost, and returns callback-ready payload dictionaries.

Current job ID policy:

`job_id = AI_JOB_{request_id}`

This deterministic MVP policy can be replaced later by UUID, sequence, database, or queue-generated job IDs.

Sensor values are normalized with the current MVP policy:

- `water_level = water_level_cm / 100.0`, clamped to `0.0` through `1.0`
- `flow_velocity = flow_velocity_mps / 1.0`, clamped to `0.0` through `1.0`

The orchestration layer does not create HTTP endpoints, send callbacks, or persist data.
The returned callback payload dictionaries also do not include `drain_id`; the backend should resolve `drain_id` through its stored `request_id` and `job_id` mapping.

Detailed request, response, callback payload, error policy, and normalization examples are documented in `ai_service/analysis/README.md`. Static documentation fixtures are available under `ai_service/analysis/examples/`.

Future HTTP endpoint code should call:

`from ai_service.analysis.service import run_analysis_job`

The `/ai/analysis/run` route should pass its parsed JSON body to `run_analysis_job(payload)` and return the `accepted_response` portion immediately.

No `ai_service/http/` runtime package exists yet because the server framework is not confirmed.

## Local Setup

Windows cmd:

```cmd
python -m venv ai_service\.venv
ai_service\.venv\Scripts\activate.bat
python -m pip install pytest
python -m pytest ai_service
```

Activate-free execution:

```cmd
ai_service\.venv\Scripts\python.exe -m pytest ai_service
```

From the repository root, package tests can be run with:

```bash
python -m pytest ai_service
```
