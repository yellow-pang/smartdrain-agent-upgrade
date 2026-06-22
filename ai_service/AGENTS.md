# AI Service Agent Guide

## Scope

All implementation work for the real YOLO/XGBoost integration must stay inside `ai_service`.

Do not edit, move, rename, or delete files outside `ai_service`, including:

- `ai-vision`
- `ai_service` sibling directories
- repository-level docs
- repository-level configuration

The existing `ai-vision/ai-decting` files are reference material only.

## Current Model Artifacts

The trained model artifacts are already placed in `ai_service/model`.

- `ai_service/model/best.pt`: trained YOLO model output
- `ai_service/model/sewer_xgboost_model.json`: trained XGBoost model output

Do not regenerate these artifacts during service integration unless explicitly requested.

## Integration Direction

The previous proof-of-concept flow was file based:

1. `ai_pipeline_v3.py` analyzed images with YOLO/OpenCV.
2. `save_to_json_v3.py` wrote `vision_v3_results.json`.
3. `xgboost_final3.py` loaded that JSON and ran XGBoost.

The service flow must be request based:

1. Backend calls `POST /ai/analysis/run`.
2. `ai_service.analysis` validates the request.
3. `ai_service.image_source` resolves a mock image source from `drain_id`.
4. YOLO analyzes the resolved local image path.
5. YOLO result is converted to the callback contract.
6. XGBoost features are built from YOLO result and sensor data.
7. XGBoost predicts final risk.
8. `ai_service.http` sends callbacks to the backend.

Do not keep `vision_v3_results.json` as a runtime dependency in `ai_service`.

## Package Boundaries

Keep these boundaries intact:

- `ai_service/http`: FastAPI routes, background task registration, callback sending, HTTP settings
- `ai_service/analysis`: orchestration, validation, YOLO/XGBoost connection, callback-ready payload creation
- `ai_service/image_source`: drain_id based image source resolution, mock source registry, future storage/CCTV source metadata
- `ai_service/yolo`: real YOLO/OpenCV predictor only
- `ai_service/xgboost`: real XGBoost predictor only
- `ai_service/model`: model artifact files

Model packages must not call backend callbacks directly.

## Naming Direction

Production YOLO code lives in:

```text
ai_service/yolo
```

The old fake predictor package has been renamed to:

```text
ai_service/yolo_legacy_example
```

It is reference/test-only code and must not be imported from production orchestration.

## Data Contracts

Backend request must include `drain_id`. The AI service resolves the image internally through `ai_service/image_source`.

```json
{
  "request_id": "REQ_001",
  "drain_id": 2,
  "sensor_data": {
    "measured_at": "2026-06-22T10:30:00+09:00",
    "water_level_cm": 98.13,
    "flow_velocity_mps": 0.4512,
    "quality_status": "valid"
  }
}
```

During the mock phase, `drain_id` values `1` through `5` resolve to mock entries with:

- `source_url`: future CCTV/storage URL placeholder
- `local_path`: local image path currently passed to YOLO

YOLO callback result contract:

```json
{
  "obstruction_ratio": 0.057,
  "confidence_score": 0.9404,
  "yolo_status": "good"
}
```

XGBoost callback result contract:

```json
{
  "risk_score": 0.65,
  "risk_level": "caution",
  "final_decision": "monitoring",
  "evaluated_at": "2026-06-22T10:30:00+09:00"
}
```

## Critical Unit Conversion

The PoC YOLO V3 logic returns obstruction ratios as percentages:

- `total_obstruction_ratio`: `0.0` to `100.0`
- `debris_ratio`: `0.0` to `100.0`
- `soil_ratio`: `0.0` to `100.0`

The trained XGBoost model expects `obstruction_ratio` in `0.0` to `1.0`.

Always convert:

```python
obstruction_ratio = total_obstruction_ratio / 100.0
```

Clamp the final value to `0.0` through `1.0`.

## Completion Rule

At the end of every work step, provide the next work prompt in chat.

The prompt must be specific enough that the next agent can continue without re-discovering the overall plan.
