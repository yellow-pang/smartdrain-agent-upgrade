# XGBoost Area Instructions

This directory owns only the XGBoost inference contract and temporary baseline predictor for SmartDrain.

## Scope

Allowed work in this directory:

- Maintain the fixed XGBoost inference input/output contract.
- Maintain validation for the dict-of-list batch input.
- Maintain the temporary rule-based baseline predictor.
- Maintain package-local tests under `ai_service/xgboost/tests/`.
- Maintain documentation for this package.

Do not add the following here:

- YOLO code or YOLO training.
- Image processing.
- Database queries.
- WebSocket implementation.
- Frontend code.
- XGBoost training code.
- Training data generation.
- `case_code`.
- Upstream/downstream cause estimation.

## Contract

The feature columns are fixed in this order:

```python
FEATURE_COLUMNS = [
    "obstruction_ratio",
    "confidence_score",
    "water_level",
    "flow_velocity",
]
```

External callers should use:

```python
from ai_service.xgboost.service import predict_flood_risk_batch
```

Keep output compatible with the current `list[dict]` contract:

- `index`
- `risk_level`
- `risk_score`
- `final_decision`
- `feature_snapshot`
- `model_version`

Allowed risk values are `good`, `caution`, `danger`, and `unknown`.

## Testing

Keep tests inside `ai_service/xgboost/tests/`.

Run package tests from the repository root:

```bash
python -m pytest ai_service/xgboost
```

`pytest.ini` keeps pytest cache inside this directory.

## Replacement Point

The trained XGBoost model should replace the predictor wiring in `service.py` and the temporary implementation in `rule_baseline_predictor.py`. Keep `validator.py`, `feature_builder.py`, constants, and the service contract stable unless the team explicitly changes the API contract.

