# Mock data

## fixtures

DB가 준비되기 전 원천 테이블 역할을 하는 고정 데이터입니다.

- `drain_data.jsonl`
- `yolo_result_data.jsonl`
- `sensor_data.jsonl`

센서 데이터는 각 YOLO `captured_at` 이전의 시계열을 포함하며, 정상·주의·위험·판단불가와 스트레스 시나리오를 재현합니다.

`yolo_result_data.jsonl`에는 `analysis_target=false`인 과거 YOLO 행이 포함될 수 있습니다. 이 행들은 pending 분석 대상이 아니라 최근 YOLO 이력 Feature 생성을 위한 목업 행입니다.

## runtime

분석 실행 시 다음 파일이 생성됩니다.

- `xgboost_data.jsonl`
- `analysis_trace.jsonl`

Git에는 포함하지 않습니다. `python scripts/reset_mock_runtime.py`로 초기화합니다.

## examples

- `expected_outcomes.jsonl`: 각 시나리오의 기대 위험 상태와 기대 상태 코드
- `example_xgboost_data.jsonl`: 전체 목업 실행 결과 예시
- `example_analysis_trace.jsonl`: Feature와 확률을 포함한 추적 예시

## 포함 시나리오

총 18개 시나리오를 포함합니다. 세부 설명은 `docs/SCENARIO_MATRIX.md`를 참조하세요.
