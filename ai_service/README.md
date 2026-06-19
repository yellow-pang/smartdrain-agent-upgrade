# SmartDrain AI Service

This directory contains the SmartDrain AI server area.

The current implementation provides the XGBoost inference contract and a temporary rule-based baseline predictor. It does not contain a trained XGBoost model.

Next steps will add analysis orchestration and a fake YOLO stub so the backend-AI server connection flow can be tested before real YOLO and model integrations are ready.

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

