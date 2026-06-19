# AI Service Area Instructions

`ai_service` is the SmartDrain AI server area.

## Modules

- `analysis` owns backend-AI asynchronous analysis orchestration.
- `_yolo` owns the temporary fake YOLO stub and is the future integration point for real YOLO.
- `xgboost` owns the flood-risk inference contract and predictor implementation.
- `http` owns backend HTTP requests, backend callback delivery, timeout, retry, and HTTP error mapping.

## Communication Boundaries

- `http` is the only layer that may receive backend HTTP requests or send backend HTTP callbacks.
- `analysis` may orchestrate `_yolo` and `xgboost`, validate payload dictionaries, and build callback-ready payload dictionaries. It must not send HTTP callbacks directly.
- `_yolo` must remain a predictor module: receive values such as `drain_id` and return YOLO result dictionaries. It must not import FastAPI, call backend APIs, send callbacks, or know backend URLs.
- `xgboost` must remain a predictor module: receive feature batches and return risk result dictionaries. It must not import FastAPI, call backend APIs, send callbacks, or know backend URLs.
- Network I/O, timeout, retry, HTTP status mapping, and callback delivery belong outside `_yolo`, `xgboost`, and `analysis`.

## Scope Rules

Do not implement the following unless the task explicitly asks for it:

- Real YOLO training or execution.
- CCTV API calls.
- Image processing.
- Real XGBoost training code.
- XGBoost model loading.
- Training data generation.
- Database reads or writes.
- WebSocket behavior.
- Frontend changes.

Keep tests under `ai_service`. Keep common pytest settings and gitignore rules at the `ai_service` level.

When changing a contract, update the relevant README, `AI_SERVICE_PLAN.md`, and tests together.

At the end of each staged task, update `ai_service/NEXT_STEP_PROMPT.md` for the next stage and also paste the same next-step prompt directly in the final chat response. Do both; do not rely on the file alone. The final chat response must let the user copy the next prompt without opening repository files. Do not use triple-backtick code fences in next-step prompts; write paths, commands, and examples as plain text or indented text so the whole prompt can be copied at once from chat.

## Commit Rules

At the end of each completed stage, commit the stage work unless the user explicitly asks not to commit.

Use this commit message format:

type: Korean description

Examples:

- `feat: AI 분석 HTTP 엔드포인트 스켈레톤 추가`
- `docs: 비동기 AI 분석 계약 기준 정리`
- `test: 비동기 AI 분석 계약 테스트 보강`

Allowed types:

- `feat`: new feature
- `fix`: bug fix
- `docs`: documentation only
- `style`: formatting or style change without logic change
- `refactor`: refactor without feature behavior change
- `test`: test code added or changed
- `chore`: build, package manager, setup, or other maintenance work
- `design`: user-facing UI design or CSS change
- `comment`: comment-only change
- `rename`: file or folder rename only
- `remove`: file deletion only
- `!HOTFIX`: urgent critical bug fix

Pick the type that best represents the main purpose of the stage. For mixed environment and documentation setup work, prefer `chore`.

## XGBoost Contract Notes

The current XGBoost feature columns are fixed in this order:

```python
FEATURE_COLUMNS = [
    "obstruction_ratio",
    "confidence_score",
    "water_level",
    "flow_velocity",
]
```

External callers should use:

```python
from ai_service.xgboost.service import predict_flood_risk_batch
```

The current XGBoost package returns `final_decision` with the same value as `risk_level`. Backend callback payload work must map this to the backend decision codes before callback delivery.
