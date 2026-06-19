# AI Service Plan

This plan tracks the SmartDrain AI service work from environment setup through real model integration.

## API Context

The backend-AI server asynchronous integration is based on three endpoints:

- `POST /ai/analysis/run`
- `POST /api/ai-callback/yolo-result`
- `POST /api/ai-callback/xgboost-result`

The backend sends `request_id`, `drain_id`, and latest sensor values. The AI server resolves image input by `drain_id`, runs YOLO, then runs XGBoost using YOLO output plus sensor values.

## Contract Gap To Resolve Later

- The current `xgboost` internal `final_decision` is the same value as `risk_level`.
- The backend callback document expects `final_decision` values of `normal`, `monitoring`, `field_check`, or `dispatch_required`.
- Callback payload generation must include a decision mapper.

## Current Stage Status

- 0단계 ai_service 개발 환경 정리 완료.
- 1단계 fake YOLO stub 추가 완료.
- `ai_service/_yolo` now provides deterministic mock YOLO results for drain IDs `1`, `2`, `3`, and `4`.
- The fake YOLO values are fixed from the first four samples of `yolo_results_json.json`.
- Fake YOLO does not read images, CCTV APIs, model files, or the external sample JSON at runtime.
- 2단계 analysis orchestration 추가 완료.
- `ai_service/analysis` now builds accepted responses, YOLO callback payloads, and XGBoost callback payloads without HTTP or DB behavior.
- 3단계 analysis 계약 세분화 및 예시 실행 문서화 완료.
- `ai_service/analysis/README.md` now documents request examples, callback payload examples, ValueError policy, sensor normalization, and decision mapping.
- `ai_service/analysis/examples/` contains static documentation fixtures.
- 4단계 HTTP API 연결 준비 범위 결정 및 스켈레톤 설계 완료.
- `ai_service/HTTP_API_DESIGN.md` documents the future `/ai/analysis/run` adapter boundary, callback sender boundary, framework status, and import path for `run_analysis_job`.
- Next stage: 5단계 HTTP endpoint 스켈레톤 구현 여부는 서버 프레임워크 확정 후 결정.

## 0단계: ai_service 개발 환경 정리

목표:
Create shared `ai_service` instructions, pytest settings, gitignore rules, a service README, this plan, and the next-step prompt.

생성/수정 예상 파일:
- `ai_service/AGENTS.md`
- `ai_service/.gitignore`
- `ai_service/pytest.ini`
- `ai_service/README.md`
- `ai_service/AI_SERVICE_PLAN.md`
- `ai_service/NEXT_STEP_PROMPT.md`
- Remove duplicate common files from `ai_service/xgboost/`

하지 않을 것:
- Do not change XGBoost inference behavior.
- Do not implement YOLO, analysis orchestration, endpoints, DB access, or callback sending.

완료 기준:
- `python -m pytest ai_service` passes.
- Common configuration is owned by `ai_service`, not `ai_service/xgboost`.
- `ai_service/NEXT_STEP_PROMPT.md` is also shown in the final chat response for quick handoff.
- Next-step prompts avoid triple-backtick code fences so they can be copied from chat in one piece.
- Stage work is committed with the repository commit type convention, for example `chore: AI 서비스 개발 환경 정리`.

## 1단계: fake YOLO stub 추가

목표:
Add a deterministic fake YOLO predictor for backend-AI flow testing before real YOLO exists.

생성/수정 예상 파일:
- `ai_service/_yolo/__init__.py`
- `ai_service/_yolo/constants.py`
- `ai_service/_yolo/fake_yolo_predictor.py`
- `ai_service/_yolo/README.md`
- `ai_service/_yolo/tests/test_fake_yolo_predictor.py`
- Update `ai_service/pytest.ini` testpaths if needed.
- Update `ai_service/NEXT_STEP_PROMPT.md` for the next stage.

하지 않을 것:
- Do not run real YOLO.
- Do not load image files.
- Do not call CCTV APIs.
- Do not add model weights.

완료 기준:
- Fake YOLO returns `obstruction_ratio`, `confidence_score`, and `yolo_status`.
- Allowed `yolo_status` values are `good`, `dirty`, `blocked`, and `unknown`.
- Tests pass with `python -m pytest ai_service`.

## 2단계: analysis orchestration 추가

목표:
Add an internal orchestration layer that accepts the backend analysis request payload, creates a job response, invokes fake YOLO, invokes XGBoost, and returns callback payload dictionaries.

생성/수정 예상 파일:
- `ai_service/analysis/__init__.py`
- `ai_service/analysis/service.py`
- `ai_service/analysis/job_id.py`
- `ai_service/analysis/schemas.py`
- `ai_service/analysis/callback_payloads.py`
- `ai_service/analysis/README.md`
- `ai_service/analysis/tests/test_analysis_flow.py`

하지 않을 것:
- Do not create FastAPI or Flask endpoints.
- Do not send real HTTP callbacks.
- Do not store jobs in a database.

완료 기준:
- A single function can process a sample backend payload and return accepted response, YOLO callback payload, and XGBoost callback payload.
- Tests pass with `python -m pytest ai_service`.

## 3단계: 백엔드 요청 payload 검증

목표:
Validate `/ai/analysis/run` request payload shape before orchestration runs.

생성/수정 예상 파일:
- `ai_service/analysis/validator.py`
- `ai_service/analysis/tests/test_analysis_validator.py`

하지 않을 것:
- Do not query backend DB.
- Do not implement HTTP status handling yet.

완료 기준:
- Required fields are validated.
- Invalid `quality_status` is rejected or handled by the documented policy.

## 4단계: YOLO callback payload 생성

목표:
Build the backend callback body for `/api/ai-callback/yolo-result`.

생성/수정 예상 파일:
- `ai_service/analysis/callback_payloads.py`
- `ai_service/analysis/tests/test_callback_payloads.py`

하지 않을 것:
- Do not send the callback over HTTP.
- Do not store YOLO results.

완료 기준:
- Payload includes `request_id`, `job_id`, and `yolo_result`.

## 5단계: XGBoost 입력 adapter 추가

목표:
Convert backend sensor fields and YOLO output into the existing XGBoost dict-of-list input contract.

생성/수정 예상 파일:
- `ai_service/analysis/xgboost_adapter.py`
- `ai_service/analysis/tests/test_xgboost_adapter.py`

하지 않을 것:
- Do not change the XGBoost service contract.
- Do not train or load a real model.

완료 기준:
- Adapter maps YOLO `obstruction_ratio`, YOLO `confidence_score`, `water_level_cm`, and `flow_velocity_mps` into XGBoost input.
- Any normalization policy is documented and tested.

## 6단계: XGBoost callback payload 생성

목표:
Build the backend callback body for `/api/ai-callback/xgboost-result`.

생성/수정 예상 파일:
- `ai_service/analysis/decision_mapper.py`
- `ai_service/analysis/callback_payloads.py`
- `ai_service/analysis/tests/test_xgboost_callback_payload.py`

하지 않을 것:
- Do not change backend DB schema.
- Do not send HTTP callbacks.

완료 기준:
- Payload includes `request_id`, `job_id`, `risk_score`, `risk_level`, mapped `final_decision`, and `evaluated_at`.

## 7단계: 통합 테스트 추가

목표:
Cover the full internal flow from backend request payload to callback payload dictionaries.

생성/수정 예상 파일:
- `ai_service/analysis/tests/test_analysis_integration.py`

하지 않을 것:
- Do not require network, DB, image files, or real model weights.

완료 기준:
- End-to-end internal tests pass with deterministic fake YOLO and rule-based XGBoost.

## 8단계: 실제 HTTP endpoint/callback sender 연결

목표:
Connect the internal orchestration to actual AI server endpoint and backend callback sender.

생성/수정 예상 파일:
- To be decided when the server framework is selected.

하지 않을 것:
- Do not change model contracts without backend agreement.

완료 기준:
- Backend can call `/ai/analysis/run`.
- AI server can send both callback payloads.

## 9단계: 실제 YOLO/CCTV API 연동

목표:
Replace fake YOLO image-source behavior with real image acquisition and YOLO inference.

생성/수정 예상 파일:
- To be decided with YOLO implementation owner.

하지 않을 것:
- Do not change backend request shape solely for image path passing.

완료 기준:
- `drain_id` resolves to real image input.
- Real YOLO output preserves the fake YOLO result contract.

## 10단계: 실제 XGBoost 모델 교체

목표:
Replace the rule-based baseline predictor with a trained XGBoost predictor while preserving the public service contract.

생성/수정 예상 파일:
- `ai_service/xgboost/xgb_predictor.py`
- `ai_service/xgboost/service.py`
- XGBoost tests and documentation as needed.

하지 않을 것:
- Do not change backend callback payloads without contract update.

완료 기준:
- Trained model predictor returns the same output contract as the current baseline.
- Existing contract tests continue to pass.
