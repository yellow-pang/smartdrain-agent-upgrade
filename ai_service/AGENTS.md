# AI Service Repository Instructions

## Repository Purpose

This repository contains the AI service work for the team flood-risk monitoring project. The active implementation scope is the XGBoost service under `xgboost/`.

There is no local YOLO implementation in this service anymore. YOLO is represented only by DB-shaped `yolo_result` input records.

## Default Work Scope

Unless the user explicitly expands the scope, make changes only in:

- `xgboost/src/flood_risk_xgb/**`
- `xgboost/tests/**`
- `xgboost/scripts/**`
- `xgboost/mock_data/**`
- `xgboost/shared/contracts/**`
- `xgboost/docs/**`
- `xgboost/requirements.txt`

Do not modify:

- root `docs/` unless the user explicitly requests it
- frontend code
- backend API code
- database DDL outside documented contract mapping
- production credentials or environment files

## Architecture Constraints

1. XGBoost must never import, execute, or directly depend on YOLO implementation code.
2. XGBoost must never load a YOLO model file.
3. `yolo_result` is an input data contract, not a local module dependency.
4. YOLO results and sensor records must be read through repository interfaces.
5. Mock JSONL repositories must remain replaceable by PostgreSQL repositories.
6. Sensor features may use only records at or before the YOLO `captured_at` timestamp.
7. `unknown` is a data-quality outcome, not a fourth XGBoost training class.
8. Model feature order must match `xgboost/models/model_metadata.json` exactly.
9. Preserve public risk codes: `good`, `caution`, `danger`, `unknown`.
10. Preserve public decision codes: `normal`, `monitoring`, `field_check`, `dispatch_required`, `review_required`.
11. Keep `state_code`, `analysis_status`, `data_quality`, and `reason_codes` separate from the XGBoost class label.
12. Do not claim real-world field performance from the included mock model.

## Environment

Existing local environment from the service root:

```powershell
cd C:\dev_work\team_proj_01\smartdrain\ai_service
.\.venv\Scripts\Activate.ps1
python xgboost\scripts\verify_setup.py
python -m pytest
deactivate
```

Install dependencies from a fresh service-root environment:

```powershell
python -m pip install -r xgboost\requirements.txt
python -m pip install -e .
```

Optional xgboost-local environment:

```powershell
cd C:\dev_work\team_proj_01\smartdrain\ai_service\xgboost
.\scripts\setup_venv.ps1
```

## Required Checks

After behavior changes:

```powershell
python xgboost\scripts\verify_setup.py
python -m pytest
```

After changing feature definitions, feature order, model metadata, or mock model training:

```powershell
python xgboost\scripts\train_mock_model.py
python xgboost\scripts\generate_mock_data.py
python xgboost\scripts\reset_mock_runtime.py
python xgboost\scripts\run_pending_analysis.py
python xgboost\scripts\verify_setup.py
python -m pytest
```

## Data Rules

- Never commit `.env`, credentials, API keys, private keys, generated runtime reports, or logs.
- Document DB-shaped field mappings in `xgboost/docs/DATA_CONTRACT.md`.
- Keep generated fixtures deterministic.
- Do not rename public fields silently.

When modifying contracts, update all relevant locations together:

- `xgboost/shared/contracts/**`
- `xgboost/docs/DATA_CONTRACT.md`
- repository adapter logic
- feature builder logic
- tests
- mock data generators

## End-of-Task Report

Report:

1. Changed files
2. Implemented behavior
3. Checks run
4. Passed, failed, and skipped checks
5. Remaining issues
6. Next recommended task
7. Next session prompt when relevant
