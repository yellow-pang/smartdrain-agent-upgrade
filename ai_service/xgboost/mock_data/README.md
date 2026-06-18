# Mock Data

이 폴더는 PostgreSQL 연동 전까지 DB 테이블 역할을 하는 JSONL 목업 데이터를 보관합니다.

## fixtures

고정 입력 데이터입니다.

- `drain_data.jsonl`
- `yolo_result_data.jsonl`
- `sensor_data.jsonl`

`yolo_result_data.jsonl`에는 분석 대상 행과 최근 YOLO 이력 행이 함께 들어 있습니다. `analysis_target=false`인 행은 pending 분석 대상이 아니라 30분 이력 Feature를 만들기 위한 과거 데이터입니다.

## runtime

분석 실행 후 생성되는 결과입니다.

- `xgboost_data.jsonl`
- `analysis_trace.jsonl`

이 파일들은 Git에 포함하지 않습니다. 초기화는 `ai_service` 루트에서 아래 명령으로 합니다.

```powershell
python xgboost\scripts\reset_mock_runtime.py
```

## examples

- `expected_outcomes.jsonl`: 18개 시나리오의 기대 `risk_level`, `state_code`
- `example_xgboost_data.jsonl`: 예시 XGBoost 결과
- `example_analysis_trace.jsonl`: Feature와 확률을 포함한 trace 예시

시나리오 설명은 `docs/SCENARIO_MATRIX.md`를 참조하세요.
