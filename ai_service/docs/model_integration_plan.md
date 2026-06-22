# Real Model Integration Plan

## Goal

Replace the current fake/rule-based AI service internals with the trained YOLO and XGBoost models stored under `ai_service/model`, while keeping the existing backend callback architecture.

Work must only modify files inside `ai_service`.

## Confirmed Artifacts

- `ai_service/model/best.pt`: trained YOLO model
- `ai_service/model/sewer_xgboost_model.json`: trained XGBoost model

The XGBoost training stage is complete and should be skipped for this integration.

## Reference Files

Reference only. Do not modify these files:

- `ai-vision/ai-decting/ai_pipeline_v3.py`
- `ai-vision/ai-decting/save_to_json_v3.py`
- `ai-vision/ai-decting/xgboost_final3.py`
- `ai-vision/ai-decting/xgboost_learn_code.py`

## Existing README Audit

The following service-local README files were reviewed before implementation planning:

- `ai_service/README.md`
- `ai_service/analysis/README.md`
- `ai_service/http/README.md`
- `ai_service/yolo_legacy_example/README.md`
- `ai_service/xgboost/README.md`
- `ai_service/HTTP_API_DESIGN.md`

Current state:

- Some older README sections still describe the original skeleton flow.
- Production analysis uses `ai_service/yolo`.
- Legacy fake YOLO examples are kept under `ai_service/yolo_legacy_example`.
- Production XGBoost service now uses `TrainedXGBoostPredictor`.
- Request examples now use `drain_id`; image resolution is handled by `ai_service/image_source`.
- The package boundary guidance is still useful and should be preserved.

Documentation update strategy:

- Do not rewrite all README files before implementation.
- Update request examples when Stage 1 changes the request contract.
- Update package names and fake/rule references after the real YOLO/XGBoost switch.
- Keep HTTP, analysis, YOLO, and XGBoost responsibility boundaries intact.
- Final README cleanup belongs to Stage 7.

## Target Runtime Flow

1. Backend calls `POST /ai/analysis/run`.
2. AI service returns accepted response immediately.
3. Background task runs the analysis pipeline.
4. `ai_service/image_source` resolves the image source by `drain_id`.
5. YOLO analyzes the resolved local image path.
6. YOLO callback payload is built.
7. XGBoost input features are built from YOLO output and sensor values.
8. XGBoost predicts risk using `sewer_xgboost_model.json`.
9. XGBoost callback payload is built.
10. HTTP layer sends both callbacks to backend.

## Stage Completion Status

- Stage 0: Complete. Service-local `AGENTS.md` and integration plan exist.
- Stage 1: Complete. `/ai/analysis/run` temporarily accepted `image_path`.
- Stage 2: Complete. `ai_service/yolo` package and YOLO contract tests exist.
- Stage 3: Complete. `ai_service/yolo/analyzer.py` implements the YOLO V3 analyzer path.
- Stage 4: Complete. `ai_service/xgboost/model_predictor.py` implements trained XGBoost inference.
- Stage 5: Complete. `analysis.service` uses `ai_service/yolo/analyzer.py` and trained XGBoost service.
- Stage 6: Complete. Runtime dependencies and Python 3.12 setup docs are documented.
- Stage 7: Complete. README cleanup and final verification were performed.
- Stage 8: Complete. Backend request contract now uses `drain_id`; `image_source` resolves mock local image paths.
- Stage 9: Complete. Legacy fake YOLO folder was renamed, README/docs were aligned, and Korean guide docs were added.
- Stage 10: Complete. Korean code comments were added at key policy boundaries and local no-callback smoke script was added.
- Stage 11: Complete. `ai_service/samples` structure and sample existence check script were added.
- Stage 12: Complete. Pre-commit checklist documentation was added for final review before committing.

Legacy code retained intentionally:

- `ai_service/yolo_legacy_example`: previous fake predictor package for reference/tests.
- `ai_service/xgboost/rule_baseline_predictor.py`: previous rule-based baseline for reference.

HTTP callback contract remains unchanged by the real model switch.

## Stage 0 - Planning Documents

Create service-local planning and agent guidance.

Deliverables:

- `ai_service/AGENTS.md`
- `ai_service/docs/model_integration_plan.md`

Acceptance:

- Documents exist under `ai_service`.
- Documents state that work must not touch files outside `ai_service`.
- Documents capture the real model integration direction.

## Stage 1 - Request Contract Update

Superseded by Stage 8. The backend no longer sends `image_path`; it sends `drain_id`.

Expected changes:

- Keep existing `request_id`, `drain_id`, and `sensor_data` contract.
- Use `ai_service/image_source` to resolve images internally.

Acceptance:

- Valid payload without `image_path` passes validation.
- Missing `request_id`, `drain_id`, or `sensor_data` still fails validation.
- Tests document the current request shape.

## Stage 2 - YOLO Package Migration

Move production YOLO code from fake-only legacy examples toward real `yolo`.

Expected changes:

- Add `ai_service/yolo`.
- Add constants and predictor modules for real YOLO.
- Migrate or replace production imports from legacy fake YOLO code to `ai_service.yolo`.
- Keep callback output contract stable.

Acceptance:

- Production analysis no longer depends on `FakeYoloPredictor`.
- YOLO predictor returns `obstruction_ratio`, `confidence_score`, and `yolo_status`.
- Tests cover unknown/error image handling.

## Stage 3 - YOLO V3 Logic Integration

Integrate the useful logic from `ai_pipeline_v3.py` into `ai_service/yolo`.

Expected changes:

- Load `ai_service/model/best.pt`.
- Read image path using OpenCV.
- Run YOLO model inference.
- Calculate debris ratio, soil ratio, and total obstruction ratio.
- Convert `total_obstruction_ratio` percent to `obstruction_ratio` unit range.
- Classify `yolo_status`.

Acceptance:

- Predictor can analyze one image path.
- Output uses `0.0` to `1.0` obstruction ratio.
- Model is loaded from `ai_service/model/best.pt`.

## Stage 4 - Real XGBoost Predictor

Replace rule-based predictor with trained XGBoost inference.

Expected changes:

- Add `ai_service/xgboost/model_predictor.py`.
- Load `ai_service/model/sewer_xgboost_model.json`.
- Preserve existing `predict_flood_risk_batch(input_dict_batch)` API if practical.
- Return the existing result keys expected by `analysis`.

Acceptance:

- XGBoost uses the trained JSON model.
- Feature order is exactly:
  - `obstruction_ratio`
  - `confidence_score`
  - `water_level`
  - `flow_velocity`
- Risk labels map to `good`, `caution`, `danger`, `unknown`.

## Stage 5 - Analysis Orchestration Switch

Connect the real YOLO and XGBoost predictors in `ai_service.analysis`.

Expected changes:

- `run_analysis_job` reads `drain_id`.
- `ai_service/image_source` resolves the source for the `drain_id`.
- YOLO predictor receives the resolved `local_path`.
- XGBoost receives feature batch from actual YOLO output and sensor values.
- Callback payload shape remains unchanged.

Acceptance:

- `/ai/analysis/run` still returns accepted response.
- Background task still sends YOLO callback first and XGBoost callback second.
- Existing callback contract remains stable.

## Stage 6 - Dependencies and Runtime Verification

Add runtime dependencies and verify service behavior.

Expected changes:

- Update `ai_service/requirements.txt`.
- Include packages needed for YOLO/OpenCV/XGBoost inference.

Expected dependencies:

- `fastapi`
- `uvicorn`
- `numpy`
- `opencv-python`
- `ultralytics`
- `pandas`
- `xgboost`
- `pytest`

Acceptance:

- Dependency install works in the project venv.
- Unit tests under `ai_service` pass.
- Local smoke test can call `POST /ai/analysis/run`.

## Stage 7 - Cleanup and Documentation

Remove fake-only production paths and update service-local docs.

Expected changes:

- Update `ai_service/README.md` and package READMEs if needed.
- Keep legacy fake YOLO examples only if clearly named as non-production code.
- Ensure production flow clearly uses real models.

Acceptance:

- No production import references `FakeYoloPredictor`.
- Docs describe the real model flow.
- Next developer can run the service from `ai_service` docs.

## Stage 8 - Drain ID Image Source Resolution

Switch the backend request from `image_path` to `drain_id` only.

Expected changes:

- Remove `image_path` from required request validation.
- Add `ai_service/image_source` with mock sources for drain IDs `1` through `5`.
- Each mock source contains `source_url` and `local_path`.
- `source_url` documents the future CCTV/storage URL.
- `local_path` is the current YOLO-readable mock image path.
- `analysis.service` resolves the image source by `drain_id`.
- Unknown `drain_id` raises `ValueError`.

Acceptance:

- Backend request examples no longer include `image_path`.
- Analysis orchestration passes the resolved `local_path` to YOLO.
- HTTP callback contract remains unchanged.

## Stage 9 - Legacy Naming and Human Docs

Clarify the production flow and remove confusing fake-only naming.

Expected changes:

- Rename the old fake YOLO package to `ai_service/yolo_legacy_example`.
- Update tests, pytest configuration, and docs to use the new package name.
- Document that unknown `drain_id` means an unregistered drain or CCTV/storage image source configuration problem.
- Check source availability before accepting the HTTP analysis job.
- Keep HTTP callback payload shape unchanged.
- Add a Korean human-facing service guide under `ai_service/docs`.

Acceptance:

- No production or test import uses the old fake YOLO package name.
- Production docs consistently point to `ai_service/yolo/analyzer.py` and `ai_service/xgboost/model_predictor.py`.
- Unknown `drain_id` is rejected before background callback processing.
- Korean guide explains folder responsibilities, request flow, mock image source policy, and local commands.

## Stage 10 - Code Comments and Local Smoke Script

Add selective Korean comments and a local model smoke command.

Expected changes:

- Review `ai_service` code and add Korean comments only where policy or data conversion needs explanation.
- Add a local smoke script that resolves image source by `drain_id`.
- The script should run analysis only when the resolved `local_path` exists.
- The script must not send backend callbacks.
- Document the smoke command and prerequisites.

Acceptance:

- Comments explain why the boundary or conversion exists, not obvious syntax.
- `python -m ai_service.scripts.smoke_analysis --drain-id 2` is documented.
- Missing local mock image exits clearly without loading YOLO.
- Compile verification succeeds.

## Stage 11 - Sample Image Placement Check

Prepare local sample image structure for real YOLO smoke tests.

Expected changes:

- Add `ai_service/samples` without adding real CCTV images.
- Document required file names:
  - `drain_1.jpg`
  - `drain_2.jpg`
  - `drain_3.jpg`
  - `drain_4.jpg`
  - `drain_5.jpg`
- Add a script that checks local sample image existence from the mock image source registry.
- Document `smoke_analysis.py` and `check_samples.py` usage.

Acceptance:

- `python -m ai_service.scripts.check_samples` reports missing sample files clearly.
- `python -m ai_service.scripts.smoke_analysis --drain-id 2` remains no-callback.
- No actual sample image is created by this stage.

## Stage 12 - Pre-Commit Checklist

Add a final review document before committing `ai_service` changes.

Expected changes:

- Add `ai_service/docs/pre_commit_checklist.md`.
- Include backend request contract checks.
- Include image source mock and sample image checks.
- Include model path checks.
- Include production and legacy package path checks.
- Include verification commands.
- Reference the checklist from README or Korean guide.

Acceptance:

- Checklist explicitly states that backend no longer sends `image_path`.
- Checklist includes compile, pytest, sample check, and no-callback smoke commands.
- No git commit is created during this stage.

## Step Completion Protocol

After each stage, the agent must provide:

- What changed
- What was verified
- Any blocker or decision needed
- The exact next work prompt
