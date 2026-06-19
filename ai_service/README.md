# SmartDrain AI Service

This directory contains the SmartDrain AI server area.

The current implementation provides analysis orchestration, a fake YOLO stub, the XGBoost inference contract, and a temporary rule-based XGBoost baseline predictor. It does not contain real YOLO execution or a trained XGBoost model.

The internal analysis flow can now build accepted responses, YOLO callback payloads, and XGBoost callback payloads without HTTP endpoints or real callback sending.

## Planned Flow

The backend-AI server integration will follow this asynchronous shape:

- `POST /ai/analysis/run`
- `POST /api/ai-callback/yolo-result`
- `POST /api/ai-callback/xgboost-result`

The AI service will receive the latest sensor values from the backend, resolve the image source internally by `drain_id`, run YOLO, run XGBoost with YOLO and sensor features, and build callback payloads.

## Current Limits

The following are not implemented yet:

- Real YOLO execution.
- CCTV API calls.
- Image processing.
- Database reads or writes.
- HTTP callback sending.
- FastAPI or Flask endpoints.
- Real XGBoost model loading or training.

## Current Fake YOLO

`ai_service/_yolo` contains deterministic mock YOLO results for MVP drain IDs `1`, `2`, `3`, and `4`. These values were copied from sample YOLO JSON output and fixed in code. The fake predictor does not read images, call CCTV APIs, load a YOLO model, or read the external sample JSON at runtime.

## Current Analysis Orchestration

`ai_service/analysis` accepts the backend analysis request shape, validates it, creates a deterministic job ID, calls fake YOLO, converts YOLO and sensor values into the XGBoost input contract, runs XGBoost, and returns callback-ready payload dictionaries.

Sensor values are normalized with the current MVP policy:

- `water_level = water_level_cm / 100.0`, clamped to `0.0` through `1.0`
- `flow_velocity = flow_velocity_mps / 1.0`, clamped to `0.0` through `1.0`

The orchestration layer does not create HTTP endpoints, send callbacks, or persist data.

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
