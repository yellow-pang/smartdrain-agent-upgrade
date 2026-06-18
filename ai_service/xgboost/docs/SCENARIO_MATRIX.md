# XGBoost 시나리오 매트릭스

`mock_data/fixtures/`에는 XGBoost 흐름을 검증하기 위한 18개 목업 상황이 들어 있습니다. 목적은 모델 성능을 증명하는 것이 아니라, 입력 조합에 따라 결과 코드가 일관되게 나오는지 확인하는 것입니다.

## 읽는 방법

각 시나리오는 아래 조합을 봅니다.

```text
YOLO 막힘 정도
YOLO 신뢰도
최근 YOLO 이력
수위 현재값과 변화량
유속 현재값과 변화량
센서 데이터 품질
```

결과는 두 축으로 확인합니다.

```text
risk_level = good | caution | danger | unknown
state_code = 왜 그렇게 판단했는지 설명하는 상황 코드
```

## 시나리오 요약

| ID | 쉬운 설명 | 기대 위험 | 기대 상태 코드 |
|---:|---|---|---|
| 1 | 막힘 없고 수위/유속 안정 | good | `NORMAL_DRAINAGE` |
| 2 | 표면 막힘은 보이나 물은 아직 잘 빠짐 | caution | `SURFACE_OBSTRUCTION_LIKELY` |
| 3 | 건조한 상태에서 표면 막힘만 보임 | caution | `DRY_SURFACE_OBSTRUCTION` |
| 4 | 표면 막힘과 수위 상승이 함께 발생 | danger | `COMBINED_OBSTRUCTION` |
| 5 | 심한 막힘, 매우 높은 수위, 거의 없는 유속 | danger | `SEVERE_OBSTRUCTION` |
| 6 | YOLO는 정상처럼 보이나 센서가 내부/하류 막힘을 의심 | danger | `INTERNAL_OR_DOWNSTREAM_OBSTRUCTION_SUSPECTED` |
| 7 | 막힘보다 유입량 과다로 수위가 오름 | caution | `HYDRAULIC_OVERLOAD` |
| 8 | 유입량 과다와 표면 막힘이 같이 있음 | caution | `HIGH_INFLOW_WITH_SURFACE_OBSTRUCTION` |
| 9 | 수위가 높지만 유속이 유지되어 버티는 상태 | caution | `NEAR_CAPACITY_STABLE` |
| 10 | 위험 상태에서 회복 중 | good | `RECOVERING` |
| 11 | 시간이 갈수록 막힘과 수위가 악화 | danger | `PROGRESSIVE_OBSTRUCTION` |
| 12 | 막힘과 센서값이 간헐적으로 흔들림 | caution | `INTERMITTENT_OBSTRUCTION` |
| 13 | YOLO 신뢰도가 낮아 판단 보류 | unknown | `LOW_CONFIDENCE_VISION` |
| 14 | 최신 수위만 비정상적으로 튀는 spike | caution/degraded | `WATER_LEVEL_SPIKE` |
| 15 | 유속 센서가 고정된 것처럼 보임 | good/degraded | `FLOW_SENSOR_STUCK` |
| 16 | 최신 센서 데이터가 너무 오래됨 | unknown | `STALE_SENSOR_DATA` |
| 17 | 유효한 센서 데이터가 없음 | unknown | `NO_VALID_SENSOR_DATA` |
| 18 | YOLO는 정상이나 센서가 숨은 위험을 감지 | danger | `SENSOR_DETECTED_HIDDEN_RISK` |

## 중요한 해석

- `unknown`은 실패가 아니라 데이터 품질 때문에 예측을 보류한 결과입니다.
- 같은 `caution`이라도 `SURFACE_OBSTRUCTION_LIKELY`, `HYDRAULIC_OVERLOAD`, `FLOW_SENSOR_STUCK`처럼 의미가 다릅니다.
- XGBoost는 YOLO 결과만 보지 않고 센서 이력과 함께 판단합니다.
- 센서값은 반드시 YOLO `captured_at` 이전 또는 같은 시점만 사용합니다.

## 검증 명령

`ai_service` 루트에서 실행합니다.

```powershell
python xgboost\scripts\verify_setup.py
python -m pytest
```

목업 결과를 직접 생성하려면:

```powershell
python xgboost\scripts\reset_mock_runtime.py
python xgboost\scripts\run_pending_analysis.py
```

결과 파일:

```text
xgboost/mock_data/runtime/xgboost_data.jsonl
xgboost/mock_data/runtime/analysis_trace.jsonl
```
