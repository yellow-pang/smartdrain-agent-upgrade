# Analysis Orchestration

`ai_service/analysis` coordinates the internal backend-AI analysis flow without creating HTTP endpoints or sending callbacks.

This package is the bridge between the backend request contract and the current fake YOLO plus XGBoost inference modules.

`run_analysis_job(payload)` is the internal entrypoint for the future `POST /ai/analysis/run` endpoint. It is not an HTTP endpoint by itself.

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

Required fields:

- `request_id`: backend-generated analysis request ID.
- `drain_id`: target drain ID. The current fake YOLO supports MVP drain IDs `1`, `2`, `3`, and `4`.
- `sensor_data.measured_at`: sensor measurement timestamp.
- `sensor_data.water_level_cm`: water level in centimeters.
- `sensor_data.flow_velocity_mps`: flow velocity in meters per second.
- `sensor_data.quality_status`: must be `valid`.

## Output

The function returns callback-ready payload dictionaries:

{
    "accepted_response": {...},
    "yolo_callback_payload": {...},
    "xgboost_callback_payload": {...},
}

The returned dictionary is for internal orchestration tests. It does not mean callbacks were sent.

`yolo_callback_payload` and `xgboost_callback_payload` are ready-to-send dictionaries only. The current implementation does not send HTTP callbacks.

## Accepted Response Example

{
    "accepted": true,
    "request_id": "REQ_20260618_001",
    "job_id": "AI_JOB_REQ_20260618_001",
    "status": "processing"
}

## Job ID Policy

The current MVP job ID is deterministic:

`job_id = AI_JOB_{request_id}`

Example:

- `request_id = REQ_20260618_001`
- `job_id = AI_JOB_REQ_20260618_001`

This can be replaced later by UUID, sequence, database job table, or queue-generated job IDs.

## YOLO Callback Payload Example

{
    "request_id": "REQ_20260618_001",
    "job_id": "AI_JOB_REQ_20260618_001",
    "yolo_result": {
        "obstruction_ratio": 0.057,
        "confidence_score": 0.9404,
        "yolo_status": "good"
    }
}

Allowed `yolo_status` values:

- `good`
- `dirty`
- `blocked`
- `unknown`

The asynchronous API source document lists `good`, `dirty`, and `blocked` for MVP. This project also allows `unknown` for fallback or status-unavailable cases.

The callback payload does not include `drain_id`. The backend must resolve the drain through its stored `request_id` and `job_id` mapping.

## XGBoost Callback Payload Example

{
    "request_id": "REQ_20260618_001",
    "job_id": "AI_JOB_REQ_20260618_001",
    "xgboost_result": {
        "risk_score": 0.65,
        "risk_level": "caution",
        "final_decision": "monitoring",
        "evaluated_at": "2026-06-19T13:30:00+09:00"
    }
}

The XGBoost callback payload also does not include `drain_id`; backend persistence should use the original request mapping.

`evaluated_at` is generated at runtime as a timezone-aware ISO string using the Korea Standard Time offset `+09:00`.

## Current Behavior

- Validates required request fields.
- Rejects sensor data unless `quality_status` is `valid`.
- Generates a deterministic job ID from `request_id`.
- Calls fake YOLO by `drain_id`.
- Converts YOLO and sensor values into the XGBoost input contract.
- Calls `predict_flood_risk_batch`.
- Maps XGBoost risk levels to backend final decision codes.

## Error Policy

The orchestration layer raises `ValueError` for invalid request payloads.

Current `ValueError` cases:

- The top-level payload is not a `dict`.
- Required top-level keys are missing: `request_id`, `drain_id`, `sensor_data`.
- `sensor_data` is not a `dict`.
- Required sensor keys are missing: `measured_at`, `water_level_cm`, `flow_velocity_mps`, `quality_status`.
- `sensor_data.quality_status` is not `valid`.

This package does not convert these errors into HTTP status codes. HTTP error mapping should be handled later by the API layer.

## Sensor Normalization

The current adapter converts backend sensor units into model features with a temporary MVP policy:

- `water_level = water_level_cm / 100.0`, clamped to `0.0` through `1.0`
- `flow_velocity = flow_velocity_mps / 1.0`, clamped to `0.0` through `1.0`

For example:

- `water_level_cm = 98.13` becomes `water_level = 0.9813`
- `flow_velocity_mps = 0.4512` becomes `flow_velocity = 0.4512`

This policy should be revisited when trained model feature scaling is finalized.

## Decision Mapping

The XGBoost package currently returns `final_decision` with the same value as `risk_level`. The backend callback contract uses separate final decision codes, so `analysis` maps risk levels before building the XGBoost callback payload.

Current mapping:

- `good` -> `normal`
- `caution` -> `monitoring`
- `danger` -> `dispatch_required`
- `unknown` -> `field_check`

## Example Files

Small static examples are available under `ai_service/analysis/examples/`.

These files are documentation fixtures only. The runtime code does not read them.

## Not Implemented

- HTTP endpoints.
- Real callback sending.
- Database persistence.
- Real YOLO.
- Real XGBoost model loading.
