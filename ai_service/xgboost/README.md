# XGBoost Inference Contract

Current version: `xgb_stub_v0`

This package does not contain a trained XGBoost model yet. It provides a temporary rule-based baseline predictor so the backend and AI server can fix the inference contract before the trained model is ready.

All current XGBoost contract code and tests are kept inside `ai_service/xgboost/`. Common pytest cache settings are managed at the `ai_service` level.

## Input

The input is a dict-of-list batch. All lists must have the same length.

```python
input_dict_batch = {
    "obstruction_ratio": yolo_obstruction_list,
    "confidence_score": yolo_confidence_list,
    "water_level": sensor_water_level_list,
    "flow_velocity": sensor_flow_velocity_list,
}
```

The feature order is fixed:

```python
FEATURE_COLUMNS = [
    "obstruction_ratio",
    "confidence_score",
    "water_level",
    "flow_velocity",
]
```

## Output

The output is `list[dict]`. Each result includes:

- `index`
- `risk_level`
- `risk_score`
- `final_decision`
- `feature_snapshot`
- `model_version`

Allowed `risk_level` and `final_decision` values are `good`, `caution`, `danger`, and `unknown`.

Rows are returned as `unknown` when any row value is `None`, any row value is `NaN`, or `confidence_score < 0.5`.

Invalid batch shapes raise `ValueError`, including missing required keys and mismatched feature list lengths.

## Scope

`case_code` is excluded from the current scope. Upstream/downstream cause estimation is also excluded.

This package does not implement YOLO execution, image processing, database access, WebSocket communication, training data generation, or XGBoost training.

## Test

Run the contract tests from the repository root:

```bash
python -m pytest ai_service
```

The shared pytest config stores pytest cache under `ai_service/.pytest_cache`.

## Future Replacement

When a trained XGBoost model is available, replace the predictor implementation currently wired in `service.py`. The input/output contract should remain stable.
