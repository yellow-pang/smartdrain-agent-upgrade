# Analysis Orchestration

`ai_service/analysis` connects request validation, image source resolution, YOLO analysis, XGBoost prediction, and callback-ready payload creation.

This package does not implement FastAPI routes or send backend callbacks directly. HTTP work stays in `ai_service/http`.

## Responsibilities

- Validate backend analysis request payloads.
- Build the immediate accepted response.
- Resolve the image source from `drain_id` through `ai_service/image_source`.
- Call the YOLO analyzer with the resolved local image path.
- Combine YOLO output with sensor data to build XGBoost features.
- Call the XGBoost predictor.
- Build YOLO and XGBoost callback payloads.
- Map `risk_level` to backend-facing `final_decision`.

## Entry Point

```python
ai_service.analysis.service.run_analysis_job(payload)
```

The FastAPI endpoint calls this function from a background task.

## Input Payload

The backend sends `drain_id`, not `image_path`. The AI service resolves the image internally.

```json
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
```

Required fields:

- `request_id`: non-empty string
- `drain_id`: integer ID or `DR-###` drain code
- `sensor_data.measured_at`: ISO datetime string with date and time, for example `2026-06-18T08:36:13+09:00`
- `sensor_data.water_level_cm`: finite numeric value
- `sensor_data.flow_velocity_mps`: finite numeric value
- `sensor_data.quality_status`: currently only `valid`

Invalid request payloads are rejected before the background task is registered.

## Image Source Resolution

`analysis.service` calls:

```python
resolve_image_source_by_drain_id(drain_id)
```

The current mock provider supports drain IDs `1` through `5`. Direct AI calls may pass either numeric IDs such as `2` or drain codes such as `DR-002`; the mock provider normalizes both to the same internal drain ID. Each source has:

- `source_url`: future CCTV/storage URL placeholder
- `local_path`: local mock image path passed to YOLO

If a drain ID is not configured, image source resolution raises `ValueError`. Treat this as an unregistered drain ID or CCTV/storage image source configuration problem.

## YOLO Flow

Production analysis uses:

```python
ai_service.yolo.analyzer.predict_yolo_by_image_path(local_path)
```

The YOLO result contract is:

```json
{
  "obstruction_ratio": 0.057,
  "confidence_score": 0.9404,
  "yolo_status": "good"
}
```

`obstruction_ratio` is a unit ratio from `0.0` to `1.0`.

If YOLO cannot produce a valid result because the image is missing, unreadable, or drain detection fails, YOLO returns sentinel values:

```json
{
  "obstruction_ratio": -1.0,
  "confidence_score": -1.0,
  "yolo_status": "unknown"
}
```

The analysis layer passes `obstruction_ratio=-1.0` and `confidence_score=-1.0` to XGBoost unchanged so the model can handle the YOLO abnormal-value scenario.

## XGBoost Feature Batch

Analysis builds this XGBoost input shape:

```python
{
    "obstruction_ratio": [obstruction_ratio],
    "confidence_score": [confidence_score],
    "water_level": [water_level],
    "flow_velocity": [flow_velocity],
}
```

Current sensor normalization:

- `water_level = water_level_cm / 100.0`
- `flow_velocity = flow_velocity_mps / 1.0`
- both values are clamped to `0.0` through `1.0`

## Return Value

`run_analysis_job(payload)` returns callback-ready payloads. It does not send callbacks itself.

```json
{
  "accepted_response": {},
  "yolo_callback_payload": {},
  "xgboost_callback_payload": {}
}
```

Callback delivery remains the responsibility of `ai_service/http`.

## Errors

`analysis` raises `ValueError` for invalid input:

- payload is not a dict
- missing `request_id`, `drain_id`, or `sensor_data`
- `request_id` is not a non-empty string
- `drain_id` is not an integer ID or `DR-###` drain code
- `sensor_data` is not a dict
- missing required sensor keys
- `sensor_data.measured_at` is not an ISO datetime string with date and time
- `sensor_data.water_level_cm` or `sensor_data.flow_velocity_mps` is not a finite number
- `quality_status` is not `valid`
- no mock image source is configured for the supplied `drain_id`

Current HTTP behavior checks image source availability before accepting the job. Request-time `ValueError` is mapped to `400 Bad Request`. Background analysis failures still do not change the callback payload shape.
