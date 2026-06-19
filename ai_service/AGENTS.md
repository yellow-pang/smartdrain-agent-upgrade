# AI Service Area Instructions

`ai_service` is the SmartDrain AI server area.

## Modules

- `analysis` owns the backend-AI server asynchronous analysis orchestration flow.
- `_yolo` owns the temporary fake YOLO stub and is the future integration point for real YOLO.
- `xgboost` owns the flood-risk inference contract and predictor implementation.

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

At the end of each staged task, update `ai_service/NEXT_STEP_PROMPT.md` for the next stage and include the same next-step prompt in the final chat response so the next task can be started without opening files. Do not use triple-backtick code fences in next-step prompts; write paths, commands, and examples as plain text or indented text so the whole prompt can be copied at once from chat.

## Commit Rules

At the end of each completed stage, commit the stage work unless the user explicitly asks not to commit.

Use this commit message format:

`type: 한글 설명`

Allowed types:

- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `docs`: 문서 수정, 코드 변경 없음
- `style`: 코드 포맷팅, 세미콜론 등 스타일 변경, 논리 변경 없음
- `refactor`: 리팩토링, 기능 변화 없음
- `test`: 테스트 관련 코드 추가 또는 수정
- `chore`: 빌드, 패키지 매니저 설정, 개발 환경 등 기타 작업
- `design`: CSS 등 사용자 UI 디자인 변경
- `comment`: 필요한 주석 추가 또는 변경
- `rename`: 파일 혹은 폴더명을 수정하거나 옮기는 작업만인 경우
- `remove`: 파일 삭제 작업만 수행한 경우
- `!HOTFIX`: 급하게 치명적인 버그를 고쳐야 하는 경우

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

The current XGBoost package returns `final_decision` with the same value as `risk_level`. Backend callback payload work must map this to the backend decision codes when that layer is implemented.
