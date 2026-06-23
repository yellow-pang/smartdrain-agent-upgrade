# YOLO Predictor

`ai_service/yolo` is the target package for the real YOLO/OpenCV image analysis integration. Production analysis uses `ai_service/yolo/analyzer.py`.

## Scope

This package should:

- Load the trained YOLO model from `ai_service/model/best.pt`.
- Analyze the local image path resolved by `ai_service/image_source`.
- Return a plain dict that matches the YOLO result contract.

This package must not:

- Send backend callbacks directly.
- Import FastAPI route code.
- Call XGBoost directly.
- Manage backend URLs, timeout, or retry behavior.

## Output Contract

Real YOLO predictors must return:

```json
{
  "obstruction_ratio": 0.057,
  "confidence_score": 0.9404,
  "yolo_status": "good"
}
```

Required fields:

- `obstruction_ratio`: blockage ratio normalized to `0.0` through `1.0`
- `confidence_score`: YOLO confidence score normalized to `0.0` through `1.0`
- `yolo_status`: one of `good`, `dirty`, `blocked`, `unknown`

## Stage 3 Note

The PoC V3 analyzer calculates `total_obstruction_ratio` as a percentage. Stage 3 must convert it before returning this package contract:

```python
obstruction_ratio = total_obstruction_ratio / 100.0
```

Clamp the value to `0.0` through `1.0`.

## Current Implementation

`ai_service/yolo/analyzer.py` provides `YoloV3ImageAnalyzer`.

Default model path:

```text
ai_service/model/best.pt
```

Production orchestration entrypoint:

```python
from ai_service.yolo.analyzer import predict_yolo_by_image_path

yolo_result = predict_yolo_by_image_path(local_path)
```

The production `analysis.service` flow receives `drain_id`, resolves it through `ai_service/image_source`, and then calls `predict_yolo_by_image_path(local_path)`.
