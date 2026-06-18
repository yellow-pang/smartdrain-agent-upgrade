너는 팀 프로젝트의 `ai_service/xgboost` 영역을 담당하는 시니어 Python/ML 엔지니어다.

현재까지 완료된 작업 요약:
- XGBoost 구현은 `ai_service/xgboost` 아래로 정리되어 있다.
- `scripts`, `mock_data`, `shared/contracts`, `docs`는 모두 `ai_service/xgboost` 하위로 이동되었다.
- 기존 `requirements/` 폴더는 제거하고 `ai_service/xgboost/requirements.txt` 단일 파일로 합쳤다.
- 로컬 YOLO PoC 코드는 제거했다.
- XGBoost는 YOLO를 실행하지 않고 외부에서 저장된 `yolo_result` 레코드만 입력으로 사용한다.

이번 작업에서 변경된 주요 파일:
- `ai_service/README.md`
- `ai_service/AGENTS.md`
- `ai_service/BUILD_INFO.md`
- `ai_service/.gitignore`
- `ai_service/xgboost/README.md`
- `ai_service/xgboost/AGENTS.override.md`
- `ai_service/xgboost/requirements.txt`
- `ai_service/xgboost/.env.example`
- `ai_service/xgboost/scripts/_bootstrap.py`
- `ai_service/xgboost/scripts/setup_venv.ps1`
- `ai_service/xgboost/scripts/setup_venv.sh`
- `ai_service/xgboost/src/flood_risk_xgb/config.py`
- `ai_service/xgboost/src/flood_risk_xgb/mock/generator.py`
- `ai_service/xgboost/src/flood_risk_xgb/training/train.py`
- `ai_service/xgboost/tests/test_model_contract.py`
- `ai_service/xgboost/tests/test_pipeline_scenarios.py`
- `ai_service/xgboost/docs/XGBOOST_SCOPE.md`
- `ai_service/xgboost/docs/SCENARIO_MATRIX.md`
- `ai_service/xgboost/mock_data/README.md`

현재 검증 상태:
- 구조 이동 후 반드시 아래 명령을 실행해 확인해야 한다.
- `python xgboost\scripts\verify_setup.py`
- `python -m pytest`

남은 이슈:
- `ai_service/START_PROMPT.md`는 과거 세션 시작용 문서라 이번 구조 정리에서는 유지되었다. 실제 작업 기준은 README와 AGENTS 문서를 우선한다.
- PostgreSQL repository adapter는 아직 실제 SQL 구현 전이다.
- 백엔드 API/WebSocket 연동은 아직 연결 전이다.

다음에 이어서 할 작업 1개:
`ai_service` 루트에서 구조 이동 후 검증을 실행하고, 실패가 있으면 경로 참조를 수정해줘.

반드시 유지할 핵심 제약:
- 루트 `docs/`는 전체 기획 문서로 유지하고 임의 수정하지 않는다.
- XGBoost는 YOLO 구현 코드나 YOLO 모델 파일을 직접 import/load하지 않는다.
- `yolo_result`는 외부 비전 분석 결과 입력 계약으로만 취급한다.
- 센서 Feature는 `yolo_result.captured_at` 이전 또는 같은 시점의 데이터만 사용한다.
- `unknown`은 XGBoost 학습 클래스가 아니라 데이터 품질 결과다.
- 모델 Feature 순서는 `xgboost/models/model_metadata.json`과 일치해야 한다.
