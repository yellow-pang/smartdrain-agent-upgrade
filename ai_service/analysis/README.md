# Analysis Orchestration

`ai_service/analysis` coordinates the internal backend-AI analysis flow without creating HTTP endpoints or sending callbacks.

## Input

`run_analysis_job(payload)` accepts the backend analysis request shape:

{
    "request_id": "REQ_20260618_001",
    "drain_id": 2,
    "sensor_data": {
        "measured_at": "2026-06-18T08:36:13+09:00",
        "water_level_cm": 98.13,
        "flow_velocity_mps": 0.4512,
        "quality_status": "valid",
    },
}

## Output

The function returns callback-ready payload dictionaries:

{
    "accepted_response": {...},
    "yolo_callback_payload": {...},
    "xgboost_callback_payload": {...},
}

## Current Behavior

- Validates required request fields.
- Rejects sensor data unless `quality_status` is `valid`.
- Generates a deterministic job ID from `request_id`.
- Calls fake YOLO by `drain_id`.
- Converts YOLO and sensor values into the XGBoost input contract.
- Calls `predict_flood_risk_batch`.
- Maps XGBoost risk levels to backend final decision codes.

## Sensor Normalization

The current adapter converts backend sensor units into model features with a temporary MVP policy:

- `water_level = water_level_cm / 100.0`, clamped to `0.0` through `1.0`
- `flow_velocity = flow_velocity_mps / 1.0`, clamped to `0.0` through `1.0`

This policy should be revisited when trained model feature scaling is finalized.

## Not Implemented

- HTTP endpoints.
- Real callback sending.
- Database persistence.
- Real YOLO.
- Real XGBoost model loading.

