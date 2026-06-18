# XGBoost area override

This is the active implementation scope.

## Allowed changes

- `xgboost/src/flood_risk_xgb/**`
- `xgboost/tests/**`
- `xgboost/models/**` when retraining the mock baseline intentionally
- XGBoost-specific scripts, mock fixtures, and documentation

## Required invariants

- Never import from `yolo/`.
- Read YOLO and sensor data through repository interfaces.
- Use only sensor records with `measured_at <= captured_at`.
- Keep `unknown` outside the trained XGBoost class set.
- Validate feature order against model metadata before inference.
- Keep mock data deterministic.
- Preserve public risk codes, decision codes, state codes, and data-quality semantics.
- Do not claim synthetic-model metrics are operational performance.

## Completion checks

Run the following after behavior changes:

```bash
python -m pytest
python scripts/verify_setup.py
```
