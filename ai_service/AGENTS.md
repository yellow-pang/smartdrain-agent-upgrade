# AI Service Repository Instructions

## Repository purpose

This repository is the AI service portion of the team flood-risk monitoring project.

It contains two physically separate areas:

* `yolo/`: a temporary legacy PoC model owned by another team member.
* `xgboost/`: the active implementation scope for the current contributor.

The service contract is database-shaped data, not direct Python imports between YOLO and XGBoost.

---

## Default work scope

Unless the user explicitly expands the scope, make changes only in:

* `xgboost/**`
* `scripts/**` when the script supports XGBoost development, mock execution, verification, or model retraining
* `mock_data/**` when updating XGBoost test fixtures or deterministic mock data
* `shared/contracts/**` only when preserving backward-compatible contracts
* `docs/**` when documenting XGBoost integration, data contracts, or repository behavior

Do not modify:

* `yolo/**` unless the user explicitly requests it
* `yolo/models/best.pt`
* frontend code
* backend API code
* database DDL outside documented contract mapping
* production credentials or environment files

Do not retrain YOLO, redesign YOLO classes, or make XGBoost depend on YOLO implementation details.

---

## Architecture constraints

1. XGBoost must never import, execute, or directly depend on code from `yolo/`.
2. XGBoost must never load `yolo/models/best.pt`.
3. YOLO results and sensor records must be read through repository interfaces.
4. The connection between YOLO and XGBoost is database-shaped data, not direct model coupling.
5. Mock JSONL repositories must remain replaceable by PostgreSQL repositories.
6. Sensor features may use only records at or before the YOLO `captured_at` timestamp.
7. Future sensor data after `captured_at` is data leakage and must not be used.
8. `unknown` is a data-quality outcome, not a fourth XGBoost training class.
9. Model feature order must match `xgboost/models/model_metadata.json` exactly.
10. Preserve the public risk codes: `good`, `caution`, `danger`, `unknown`.
11. Preserve the public decision codes: `normal`, `monitoring`, `field_check`, `dispatch_required`, `review_required`.
12. Keep `state_code`, `analysis_status`, `data_quality`, and `reason_codes` separate from the XGBoost class label.
13. Treat included model metrics as synthetic mock-development evidence only.
14. Do not claim real-world field performance from the included mock model.

---

## Development environment

All commands assume the current working directory is the AI service repository root.

Create the repository-local virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment.

Linux/macOS/Git Bash:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the XGBoost development environment:

```bash
python -m pip install -r requirements/dev.txt
python -m pip install -e .
```

---

## Required pre-work checks

Before making code changes, inspect the current structure and relevant modules first.

Recommended commands:

```bash
python scripts/verify_setup.py
python -m pytest
```

If these commands fail before any change, record the failure as the baseline state before editing.

---

## Required checks after changes

After changing XGBoost behavior, run:

```bash
python scripts/verify_setup.py
python -m pytest
```

When changing feature definitions, feature order, model input schema, or model metadata, also run:

```bash
python scripts/train_mock_model.py
python scripts/generate_mock_data.py
python scripts/reset_mock_runtime.py
python scripts/run_pending_analysis.py
python scripts/verify_setup.py
python -m pytest
```

If a check cannot be executed, report:

* which command was not executed
* why it was not executed
* what risk remains because it was skipped

---

## Data and security rules

* Never commit `.env`, credentials, database passwords, API keys, private keys, or generated runtime reports.
* Do not treat mock-model metrics as real-world performance evidence.
* Do not silently change DB field names.
* Document DB-shaped field mappings in `docs/DATA_CONTRACT.md`.
* Prefer deterministic mock data and fixed random seeds.
* Keep generated test fixtures reproducible.
* Do not introduce hidden network calls in tests unless explicitly required.

---

## Contract change rules

When modifying data contracts, preserve backward compatibility whenever possible.

If a contract change is unavoidable, update all relevant locations together:

* `shared/contracts/**`
* `docs/DATA_CONTRACT.md`
* repository adapter logic
* feature builder logic
* tests
* mock data generators
* example runtime reports, if applicable

Do not rename public fields silently.

---

## XGBoost feature rules

Feature generation must remain independent from YOLO implementation details.

Allowed inputs:

* YOLO result records
* sensor records
* recent YOLO history records
* deterministic derived features
* data-quality flags

Forbidden inputs:

* YOLO model internals
* YOLO training labels not present in the DB-shaped contract
* image tensors
* image preprocessing outputs not stored in the contract
* sensor records after `yolo_result.captured_at`

Feature order must remain synchronized with:

```text
xgboost/models/model_metadata.json
```

If the feature list changes, retrain the mock baseline and regenerate metadata.

---

## Runtime output rules

Do not commit generated runtime outputs unless the user explicitly requests it.

Generated outputs may include:

* temporary analysis reports
* local runtime JSONL files
* model experiment artifacts
* cache files
* logs

If a generated artifact is needed as a fixture, place it under the appropriate mock or test fixture directory and keep it deterministic.

---

## Task workflow

For each task, follow this order:

```text
1. Inspect current file structure.
2. Inspect related modules before editing.
3. Propose the minimal change scope.
4. Implement the requested change.
5. Run required checks.
6. Report changed files.
7. Report passed, failed, and skipped checks.
8. Document unresolved design or operation issues.
9. Generate the next-session prompt when relevant.
```

Avoid broad refactoring unless the user explicitly requests it.

If a large refactor is needed, propose it as a separate next task instead of mixing it into the current change.

---

## End-of-task report format

At the end of each implementation task, report using this structure:

```text
1. Summary
2. Changed files
3. Implemented behavior
4. Checks run
5. Test results
   - Passed:
   - Failed:
   - Not run:
6. Remaining issues
7. Next recommended task
8. Next session prompt
```

Be concise and factual. Do not include internal reasoning.

---

## Next session prompt rule

When the task ends, create or update:

```text
xgboost/NEXT_SESSION_PROMPT.md
```

This file should contain only the prompt needed for the next coding session.

It should include:

* current completed work
* files changed in the latest session
* current verification status
* remaining issues
* the highest-priority next task
* architecture constraints that must remain unchanged

Do not continue into the next task automatically after generating the prompt.

---

## Priority rule

When instructions conflict, follow this priority order:

```text
1. User's explicit current request
2. Safety and security rules
3. Architecture constraints
4. Data contract compatibility
5. Test and verification requirements
6. Code style and cleanup
```

When uncertain, choose the smallest safe change that preserves the existing architecture.
