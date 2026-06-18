# Implementation summary — v2 changes from uploaded base

## 분석 기준

업로드된 `ai_service_xgboost_mock_v1` 구조는 이미 다음 장점을 갖고 있었다.

- `ai_service/yolo`와 `ai_service/xgboost`가 분리되어 있었다.
- XGBoost가 YOLO 코드를 직접 import하지 않는 repository 구조였다.
- JSONL 목업 저장소를 통해 DB 없이 분석 흐름을 실행할 수 있었다.
- 최신 센서값과 5분/30분 센서 이력을 Feature로 사용했다.
- 품질 게이트와 baseline XGBoost 모델이 포함되어 있었다.

이번 버전에서는 위 구조를 유지하면서, 지금까지 논의한 실제 시나리오와 운영 해석을 더 반영했다.

## 주요 반영 사항

### 1. Feature 확장

기존 Feature에 다음을 추가했다.

```text
obstruction_mean_30m
obstruction_delta_30m
obstruction_persistence_count_30m
water_level_slope_30m
flow_velocity_slope_30m
water_level_std_30m
flow_velocity_std_30m
sensor_valid_ratio_30m
```

이제 XGBoost는 현재값뿐 아니라 YOLO 막힘 지속성, 수위·유속 변화 기울기, 센서 유효 비율을 참고한다.

### 2. 센서 이상 탐지 추가

`policy/sensor_diagnostics.py`를 추가해 다음 이상을 감지한다.

```text
NO_VALID_SENSOR_DATA
STALE_SENSOR_DATA
WATER_LEVEL_SPIKE
FLOW_SENSOR_STUCK
SENSOR_OSCILLATION
```

이상값은 무조건 XGBoost 위험 클래스로 밀어 넣지 않고 `data_quality`, `analysis_status`, `state_code`로 별도 기록한다.

### 3. 상태 코드 분리

기존에는 `risk_level` 중심이었다. 이번 버전은 `risk_level`과 `state_code`를 분리한다.

예:

```text
risk_level = caution
state_code = SURFACE_OBSTRUCTION_LIKELY
```

```text
risk_level = danger
state_code = INTERNAL_OR_DOWNSTREAM_OBSTRUCTION_SUSPECTED
```

이 구조는 “YOLO는 막힘인데 센서는 정상”, “YOLO는 정상인데 센서는 위험”, “상부만 막힘”, “센서 이상값” 같은 경우의 수를 표현하기 위한 것이다.

### 4. 최종 대응 코드 정리

최종 대응 코드를 다음으로 정리했다.

```text
normal
monitoring
field_check
dispatch_required
review_required
```

### 5. 목업 시나리오 확장

기존 12개 시나리오를 18개로 확장했다.

```text
정상 배수
상부만 막힘
건조 상태 상부 이물질
상부·내부 복합 막힘
심각한 완전 막힘
YOLO 정상이나 내부·하류 막힘
과도한 유입
과도한 유입 + 상부 막힘
용량 근접 안정 상태
위험 상태 회복 중
진행성 막힘
간헐적 막힘
YOLO 오탐 의심
수위 센서 spike
유속 센서 stuck
센서 데이터 지연
유효 센서 데이터 없음
YOLO 정상·센서 숨은 위험
```

## 검증 결과

```text
python scripts/verify_setup.py → 통과, 18 / 18 시나리오 검증
python -m pytest → 8 passed
```

## 남은 팀 결정 사항

실제 DB 연동 전 다음은 팀 합의가 필요하다.

- 결과 테이블명을 `xgboost_data`로 할지 `report_data`로 할지
- `state_code`, `analysis_status`, `data_quality`, `reason_codes`를 결과 테이블에 직접 둘지 trace 테이블에 둘지
- `obstruction_ratio`의 정확한 의미
- 실제 위험 정답 라벨 출처
- XGBoost 실행 트리거 방식
