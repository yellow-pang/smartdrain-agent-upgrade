# AI Service Plan

This plan tracks the SmartDrain AI service work from environment setup through real model integration.

## API Context

The backend-AI server asynchronous integration is based on three endpoints:

- `POST /ai/analysis/run`
- `POST /api/ai-callback/yolo-result`
- `POST /api/ai-callback/xgboost-result`

The backend sends `request_id`, `drain_id`, and latest sensor values. The AI server resolves image input by `drain_id`, runs YOLO, then runs XGBoost using YOLO output plus sensor values.

The agreed local ports are:

- AI server: `9000`
- Backend server: `8000`

## Responsibility Boundary

- `ai_service/http` handles HTTP endpoint input and backend callback delivery.
- `ai_service/analysis` validates and orchestrates dictionaries, then builds callback-ready payloads.
- `ai_service/_yolo` returns fake or future real YOLO result dictionaries only.
- `ai_service/xgboost` returns flood-risk inference result dictionaries only.

`_yolo`, `xgboost`, and `analysis` must not send callbacks or know backend URLs.

## Current Stage Status

- Stage 0 complete: `ai_service` development environment and shared instructions.
- Stage 1 complete: fake YOLO stub for drain IDs `1`, `2`, `3`, and `4`.
- Stage 2 complete: internal analysis orchestration.
- Stage 3 complete: analysis contract and examples documented.
- Stage 4 complete: HTTP API design documented.
- Stage 5 complete: endpoint implementation was deferred until framework confirmation.
- API contract alignment complete: asynchronous backend-AI API document reflected in service docs.
- Contract tests complete: async API contract tests added.
- Current implementation complete: FastAPI `/ai/analysis/run` skeleton and best-effort callback sender.
- Current test hardening complete: callback flow tests verify YOLO callback URL, XGBoost callback URL, failure continuation, analysis failure handling, and `BACKEND_BASE_URL` override.

## Contract Notes

- `job_id` MVP policy: `AI_JOB_{request_id}`.
- YOLO status values: `good`, `dirty`, `blocked`, `unknown`.
- XGBoost risk levels: `good`, `caution`, `danger`, `unknown`.
- Backend `final_decision` values: `normal`, `monitoring`, `field_check`, `dispatch_required`.
- Current XGBoost internal `final_decision` equals `risk_level`; analysis maps it to backend decision codes before callback payload delivery.
- Callback delivery is best-effort in MVP. A failed callback is logged and does not change the already accepted response.

## Stage 0: ai_service Development Environment

Goal:
Create shared `ai_service` instructions, pytest settings, gitignore rules, service README, plan, and next-step prompt.

Expected files:

- `ai_service/AGENTS.md`
- `ai_service/.gitignore`
- `ai_service/pytest.ini`
- `ai_service/README.md`
- `ai_service/AI_SERVICE_PLAN.md`
- `ai_service/NEXT_STEP_PROMPT.md`

Do not:

- Change XGBoost inference behavior.
- Implement YOLO, analysis orchestration, endpoints, DB access, or callback sending.

Done when:

- `python -m pytest ai_service` passes.
- Common configuration is owned by `ai_service`, not `ai_service/xgboost`.

## Stage 1: Fake YOLO Stub

Goal:
Add a deterministic fake YOLO predictor for backend-AI flow testing before real YOLO exists.

Expected files:

- `ai_service/_yolo/__init__.py`
- `ai_service/_yolo/constants.py`
- `ai_service/_yolo/fake_yolo_predictor.py`
- `ai_service/_yolo/README.md`
- `ai_service/_yolo/tests/test_fake_yolo_predictor.py`

Do not:

- Run real YOLO.
- Load image files.
- Call CCTV APIs.
- Add model weights.

Done when:

- Fake YOLO returns `obstruction_ratio`, `confidence_score`, and `yolo_status`.
- Tests pass with `python -m pytest ai_service`.

## Stage 2: Analysis Orchestration

Goal:
Add an internal orchestration layer that accepts backend request payloads, creates a job response, invokes fake YOLO, invokes XGBoost, and returns callback payload dictionaries.

Expected files:

- `ai_service/analysis/__init__.py`
- `ai_service/analysis/service.py`
- `ai_service/analysis/job_id.py`
- `ai_service/analysis/callback_payloads.py`
- `ai_service/analysis/validator.py`
- `ai_service/analysis/tests/test_analysis_flow.py`

Do not:

- Create HTTP endpoints.
- Send real HTTP callbacks.
- Store jobs in a database.

Done when:

- A single function can process a sample backend payload and return accepted response, YOLO callback payload, and XGBoost callback payload.
- Tests pass with `python -m pytest ai_service`.

## Stage 3: Analysis Contract Documentation

Goal:
Document request examples, accepted response, callback payloads, error policy, sensor normalization, and decision mapping.

Expected files:

- `ai_service/analysis/README.md`
- `ai_service/analysis/examples/*`

Do not:

- Add network, DB, endpoint, or real model behavior.

Done when:

- The backend contract can be reviewed from repository docs.
- Tests pass with `python -m pytest ai_service`.

## Stage 4: HTTP API Design

Goal:
Document how `/ai/analysis/run` connects to `run_analysis_job(payload)` and how callback sending is owned by the HTTP layer.

Expected files:

- `ai_service/HTTP_API_DESIGN.md`
- `ai_service/README.md`

Do not:

- Implement endpoint code until framework confirmation.

Done when:

- Endpoint boundary, callback boundary, and framework decision criteria are documented.
- Tests pass with `python -m pytest ai_service`.

## Stage 5: FastAPI Endpoint Skeleton

Goal:
Expose `POST /ai/analysis/run` using FastAPI after framework confirmation.

Expected files:

- `ai_service/http/app.py`
- `ai_service/http/routes.py`
- `ai_service/http/config.py`
- `ai_service/http/callback_sender.py`
- `ai_service/http/README.md`
- `ai_service/http/tests/*`
- `ai_service/requirements.txt`

Do not:

- Implement real YOLO.
- Call CCTV APIs.
- Store to DB.
- Change XGBoost public contract.

Done when:

- The endpoint validates request payloads.
- The endpoint immediately returns accepted response.
- Background processing sends YOLO and XGBoost callback payloads through a best-effort callback sender.
- Tests pass with `python -m pytest ai_service`.

## Next Work Candidates

1. Run manual smoke testing with the backend running on port `8000` and AI server on port `9000`.
2. Add callback failure observability if the backend team needs clearer logs or metrics.
3. Decide whether failed callbacks need a retry queue beyond the MVP best-effort sender.
4. Later, replace fake YOLO and rule-based XGBoost only after their contracts are stable.
