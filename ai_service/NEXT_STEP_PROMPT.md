# Next Step Prompt

You are a Python engineer responsible for the `ai_service/` area of the team project.

This task is **manual backend-AI smoke test execution or callback failure observability planning**.

Before working, read the repository root `AGENTS.md` if it exists. Also read and follow `ai_service/AGENTS.md`.

Check the current file structure before making changes. Keep changes small and consistent with the existing structure.

After completing the task, commit according to the commit rules in `ai_service/AGENTS.md`.

## Current State

FastAPI HTTP skeleton exists and callback flow tests are covered.

AI server endpoint:

POST /ai/analysis/run

Run command:

python -m uvicorn ai_service.http.app:app --host 0.0.0.0 --port 9000 --reload

Backend base URL default:

http://localhost:8000

Callback endpoints:

POST /api/ai-callback/yolo-result
POST /api/ai-callback/xgboost-result

## Responsibility Boundary

Backend HTTP communication must happen only in `ai_service/http`.

`analysis` only orchestrates and builds callback-ready payload dictionaries.

`_yolo` is predictor-only: it receives `drain_id` and returns a YOLO result dictionary.

`xgboost` is predictor-only: it receives feature batches and returns risk result dictionaries.

## Work Candidates

1. Run a manual smoke test with the real backend server on port `8000` and AI server on port `9000`.
2. If the backend is not available, document the exact manual smoke-test checklist and expected callback payloads.
3. Decide whether MVP callback failures need only logging or a future retry queue design.

## Do Not

- Implement real YOLO.
- Change fake YOLO mock values.
- Implement image processing.
- Call CCTV APIs.
- Train or load a real XGBoost model.
- Read or write the database.
- Implement WebSocket behavior.
- Modify frontend code.
- Change the XGBoost public contract.

## Verification

For HTTP-only changes, first run:

ai_service\.venv\Scripts\python.exe -m pytest ai_service\http

Before committing, run:

ai_service\.venv\Scripts\python.exe -m pytest ai_service

## Completion

After finishing, update `ai_service/NEXT_STEP_PROMPT.md` for the next stage.

Do not use triple-backtick code fences in the next-step prompt.

Report:

- Created or modified files
- Chosen work direction
- Test result
- Commit hash and commit message
- Whether the next stage can start

Keep changes small, follow existing style, and avoid unnecessary abstractions.
