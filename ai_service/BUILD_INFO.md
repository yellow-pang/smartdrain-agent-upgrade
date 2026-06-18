# Build information

- Build date: 2026-06-18
- Package scope: XGBoost development scaffold with a temporary legacy YOLO PoC model
- Source basis: uploaded `ai_service_xgboost_mock_v1` folder + latest architecture/scenario requirements
- Data source: deterministic JSONL mock repositories
- XGBoost model: synthetic development baseline (`xgb-mock-v2.0.0`)
- Automated tests: 8 passed
- Deterministic scenario verification: 18 / 18 passed
- Virtual environment: not bundled; create `.venv` after extraction

## Validation commands

```bash
python -m pytest
python scripts/verify_setup.py
```

## Important limitation

The included model and metrics are based on synthetic data and are intended only for integration and pipeline development. They are not operational performance evidence.
