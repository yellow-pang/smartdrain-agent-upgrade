# XGBoost Predictor

`ai_service/xgboost` is the predictor-only package for final flood-risk inference.

Production flow uses:

```text
ai_service/xgboost/model_predictor.py
```

Default model artifact:

```text
ai_service/model/sewer_xgboost_model.json
```

## Responsibility

This package should:

- Accept a fixed feature batch.
- Run XGBoost inference.
- Return risk result dictionaries.

This package must not:

- Send backend callbacks.
- Import FastAPI route code.
- Call YOLO directly.
- Manage backend URLs, timeout, or retry behavior.

Callback delivery remains the responsibility of `ai_service/http`.

## Input Contract

Input is a dict-of-list batch. All lists must have the same length.

```python
input_dict_batch = {
    "obstruction_ratio": [0.061],
    "confidence_score": [0.8504],
    "water_level": [0.85],
    "flow_velocity": [0.05],
}
```

Feature order must remain:

```python
FEATURE_COLUMNS = [
    "obstruction_ratio",
    "confidence_score",
    "water_level",
    "flow_velocity",
]
```

YOLO abnormal-value scenario:

- If YOLO cannot produce a valid image analysis result, `obstruction_ratio` is `-1.0`.
- In the same case, `confidence_score` is `-1.0`.
- XGBoost receives these sentinel values unchanged.

## Output Contract

`predict_flood_risk_batch(input_dict_batch)` returns `list[dict]`.

Each row contains:

- `index`
- `risk_level`
- `risk_score`
- `final_decision`
- `feature_snapshot`
- `model_version`

Example:

```json
[
  {
    "index": 0,
    "risk_level": "danger",
    "risk_score": 0.93,
    "final_decision": "danger",
    "feature_snapshot": {
      "obstruction_ratio": 0.88,
      "confidence_score": 0.94,
      "water_level": 0.82,
      "flow_velocity": 0.13
    },
    "model_version": "sewer_xgboost_model_v1"
  }
]
```

Allowed `risk_level` values:

- `good`
- `caution`
- `danger`
- `unknown`

Label mapping follows the training code:

| label index | risk_level |
| ---: | --- |
| 0 | `good` |
| 1 | `caution` |
| 2 | `danger` |
| 3 | `unknown` |

`final_decision` is intentionally returned as the same value as `risk_level`; backend callback decision mapping is handled by `ai_service/analysis`.

## Tests

Run from repository root after installing dependencies:

```powershell
python -m pytest ai_service
```
