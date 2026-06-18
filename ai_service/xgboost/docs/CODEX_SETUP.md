# Codex Setup

- `ai_service/AGENTS.md` describes the AI service boundary.
- `xgboost/AGENTS.override.md` applies the local XGBoost rules.
- Root `docs/` is the project-wide planning document area and should stay read-only unless explicitly requested.
- XGBoost work should normally stay inside `ai_service/xgboost/**`.

Recommended verification from `ai_service` root:

```powershell
python xgboost\scripts\verify_setup.py
python -m pytest
```
