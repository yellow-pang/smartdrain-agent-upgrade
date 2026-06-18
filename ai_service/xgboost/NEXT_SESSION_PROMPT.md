너는 팀 프로젝트의 `ai_service` 영역 중 `xgboost/`를 담당하는 시니어 Python/ML 엔지니어다.

현재까지 완료된 작업:
- 루트 `docs/`의 MVP/ERD/API 흐름과 현재 `ai_service/xgboost` 구현을 비교했다.
- 백엔드와 DB 연동 전에 확정해야 할 XGBoost 데이터 계약 항목을 문서화했다.
- 권장 표준안은 `xgboost_data` 테이블명 유지, DB/API 이미지 필드는 `image_url`, XGBoost 내부 alias는 `image_uri`, `final_decision`은 현재 공개 코드 세트 유지, `unknown` 결과의 `risk_score`와 `sensor_measured_at` nullable 허용이다.
- `state_code`, `analysis_status`, `data_quality`, `reason_codes`는 결과 조회에 포함하고, Feature 스냅샷과 확률 등 재현 정보는 별도 trace 테이블 또는 JSON 컬럼으로 분리하는 방향을 권장했다.

이번 세션에서 변경된 파일:
- `ai_service/docs/DB_INTEGRATION_NOTES.md`
- `ai_service/docs/DATA_CONTRACT.md`
- `ai_service/docs/DECISIONS_PENDING.md`
- `ai_service/xgboost/NEXT_SESSION_PROMPT.md`

현재 검증 상태:
- 문서만 수정했고 XGBoost 코드, 모델, fixture, 계약 JSON schema는 변경하지 않았다.
- 테스트는 실행하지 않았다.
- 최근 환경 기준 검증은 `python scripts/verify_setup.py` 18/18 통과, `python -m pytest` 8 passed 상태였다.

남은 이슈:
- 백엔드/DB 담당자와 `xgboost_data` 실제 컬럼, nullable 정책, trace 저장 방식, 실행 트리거를 확정해야 한다.
- PostgreSQL repository adapter는 아직 실제 SQL 구현이 없다.
- 루트 ERD의 `final_decision` 예시 코드와 현재 XGBoost 공개 코드 세트가 다르므로 팀 표준 확정이 필요하다.

다음 작업 요청:
`ai_service/docs/DB_INTEGRATION_NOTES.md`의 권장 표준안을 기준으로 PostgreSQL repository adapter 구현 전에 필요한 SQLAlchemy/DB 매핑 체크리스트와 adapter 구현 계획을 작성해줘. 코드 구현은 아직 하지 말고 문서 중심으로 정리해줘.

반드시 유지할 핵심 제약:
- XGBoost는 `yolo/` 내부 코드를 import하거나 실행하지 않는다.
- XGBoost는 `yolo/models/best.pt`를 직접 로드하지 않는다.
- YOLO와 XGBoost는 DB-shaped 데이터 계약으로만 연결한다.
- 센서 Feature는 `yolo_result.captured_at` 이전 또는 같은 시점의 데이터만 사용한다.
- `unknown`은 XGBoost 학습 클래스가 아니라 데이터 품질 결과다.
- 모델 Feature 순서는 `xgboost/models/model_metadata.json`과 일치해야 한다.
- 루트 `docs/`는 전체 기획 문서로 유지하고 임의 수정하지 않는다.
