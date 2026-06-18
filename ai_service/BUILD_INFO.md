# Build Information

- Build date: 2026-06-18
- Package scope: XGBoost development scaffold
- Local YOLO code: removed
- YOLO dependency shape: external `yolo_result` records only
- Data source: deterministic JSONL mock repositories
- XGBoost model: synthetic development baseline (`xgb-mock-v2.0.0`)
- Previous automated tests: 8 passed
- Previous deterministic scenario verification: 18 / 18 passed

## Validation Commands

Run from `ai_service` root:

```powershell
python xgboost\scripts\verify_setup.py
python -m pytest
```

## Important Limitation

The included model and metrics are based on synthetic data and are intended only for integration and pipeline development. They are not operational performance evidence.
