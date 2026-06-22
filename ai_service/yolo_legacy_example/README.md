# Legacy YOLO Example

`ai_service/yolo_legacy_example` is not production YOLO code.

This package keeps the old deterministic fake YOLO predictor as a reference and test example. It exists so older flow tests and mock-result examples remain easy to inspect without confusing them with the real runtime package.

Production analysis uses:

```text
ai_service/yolo/analyzer.py
```

## Current Mock Behavior

`fake_yolo_predictor.py` accepts `drain_id` and returns a predefined YOLO-like result.

Supported legacy mock drain IDs:

- `1`
- `2`
- `3`
- `4`

Unknown drain IDs return an `unknown` YOLO result in this legacy example. This differs from the current production image source policy, where unknown `drain_id` raises `ValueError` before YOLO runs.

## Responsibility Boundary

This package must remain predictor-only example code.

It must not:

- send backend callbacks
- import FastAPI route code
- call XGBoost directly
- manage backend URLs, timeout, or retry behavior

Callback payload creation belongs to `ai_service/analysis`. Callback delivery belongs to `ai_service/http`.

## Output Contract

The legacy fake predictor returns the same YOLO result fields used by production:

```json
{
  "obstruction_ratio": 0.061,
  "confidence_score": 0.8504,
  "yolo_status": "good"
}
```

Allowed `yolo_status` values:

- `good`
- `dirty`
- `blocked`
- `unknown`

## Legacy Mock Values

| drain_id | obstruction_ratio | confidence_score | yolo_status |
| ---: | ---: | ---: | --- |
| 1 | 0.0227 | 0.676 | good |
| 2 | 0.057 | 0.9404 | good |
| 3 | 0.002 | 0.9371 | good |
| 4 | 0.061 | 0.8504 | good |

Do not import this package from production orchestration.
