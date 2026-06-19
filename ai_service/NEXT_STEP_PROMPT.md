# Next Step Prompt

You are a Python engineer responsible for the `ai_service/` area of the team project.

This task is **callback sender integration test hardening or backend smoke-test preparation**.

Before working, read the repository root `AGENTS.md` if it exists. Also read and follow `ai_service/AGENTS.md`.

Check the current file structure before making changes. Keep changes small and consistent with the existing structure.

After completing the task, commit according to the commit rules in `ai_service/AGENTS.md`.

## Current State

FastAPI HTTP skeleton exists.

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

1. Harden callback sender integration tests.
2. Document smoke-test steps for when the real backend server is running.
3. Add or clarify callback sender logging policy documentation.

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

The following command must pass:

python -m pytest ai_service

venv command:

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
