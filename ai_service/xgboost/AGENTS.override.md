# XGBoost Area Override

This is the active implementation scope.

## Allowed Changes

- `src/flood_risk_xgb/**`
- `tests/**`
- `scripts/**`
- `mock_data/**`
- `shared/contracts/**`
- `docs/**`
- `models/**` only when retraining the mock baseline intentionally
- `requirements.txt`

## Required Invariants

- Do not import or execute YOLO implementation code.
- Treat `yolo_result` as an external input record contract only.
- Read YOLO and sensor data through repository interfaces.
- Use only sensor records with `measured_at <= captured_at`.
- Keep `unknown` outside the trained XGBoost class set.
- Validate feature order against model metadata before inference.
- Keep mock data deterministic.
- Preserve public risk codes, decision codes, state codes, and data-quality semantics.
- Do not claim synthetic-model metrics are operational performance.

## Completion Checks

Run after behavior changes from `ai_service` root:

```powershell
python xgboost\scripts\verify_setup.py
python -m pytest
```
