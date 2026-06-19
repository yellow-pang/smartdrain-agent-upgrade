# Analysis Orchestration

`ai_service/analysis`는 백엔드 요청, YOLO 단계, XGBoost 단계, callback payload 생성을 연결하는 오케스트레이션 계층이다.

이 계층은 실제 YOLO/XGBoost 모델을 직접 구현하는 곳이 아니다. 모델 predictor를 호출하고, 각 단계의 입출력 계약을 연결하는 역할만 한다.

## 책임

`analysis` 계층이 담당하는 일:

- 백엔드 요청 payload 검증
- accepted response 생성
- `drain_id` 기준 YOLO 단계 호출
- YOLO 결과와 센서값을 조합해 XGBoost 입력 feature 생성
- 센서값 정규화
- XGBoost 단계 호출
- XGBoost 결과를 백엔드 callback contract에 맞게 변환
- YOLO callback payload 생성
- XGBoost callback payload 생성
- `final_decision` mapping

`analysis` 계층이 하면 안 되는 일:

- HTTP 요청을 직접 받기
- 백엔드 callback 직접 전송
- FastAPI import
- backend URL 관리
- callback timeout/retry 처리
- DB 저장
- 실제 YOLO 모델 로딩
- 실제 XGBoost 모델 로딩

HTTP 통신은 `ai_service/http` 계층의 책임이다.

## 내부 entrypoint

현재 내부 진입점:

`ai_service.analysis.service.run_analysis_job(payload)`

이 함수는 `POST /ai/analysis/run` endpoint에서 호출된다. 단, 이 함수 자체는 HTTP endpoint가 아니다.

## 입력 payload

`run_analysis_job(payload)`는 백엔드 분석 요청 형태의 dict를 받는다.

```json
{
  "request_id": "REQ_20260618_001",
  "drain_id": 2,
  "sensor_data": {
    "measured_at": "2026-06-18T08:36:13+09:00",
    "water_level_cm": 98.13,
    "flow_velocity_mps": 0.4512,
    "quality_status": "valid"
  }
}
```

필수 필드:

- `request_id`: 백엔드가 생성한 분석 요청 ID
- `drain_id`: 분석 대상 빗물받이 ID
- `sensor_data.measured_at`: 센서 측정 시각
- `sensor_data.water_level_cm`: 수위, centimeter 단위
- `sensor_data.flow_velocity_mps`: 유속, meter per second 단위
- `sensor_data.quality_status`: 현재는 `valid`만 허용

## 반환값

`run_analysis_job(payload)`는 내부 테스트와 HTTP 계층 전달을 위해 아래 dict를 반환한다.

```json
{
  "accepted_response": {},
  "yolo_callback_payload": {},
  "xgboost_callback_payload": {}
}
```

주의:

- 이 반환값은 callback이 실제로 전송됐다는 뜻이 아니다.
- `analysis`는 callback-ready payload만 만든다.
- 실제 callback 전송은 `ai_service/http` 계층에서 수행한다.

accepted response 예시:

```json
{
  "accepted": true,
  "request_id": "REQ_20260618_001",
  "job_id": "AI_JOB_REQ_20260618_001",
  "status": "processing"
}
```

## YOLO 단계 연결

현재 YOLO 단계는 실제 모델이 아니라 아래 fake predictor를 사용한다.

`ai_service/_yolo/fake_yolo_predictor.py`

`analysis`는 `drain_id`를 기준으로 YOLO predictor를 호출하고 아래 결과를 받는다고 가정한다.

- `obstruction_ratio`
- `confidence_score`
- `yolo_status`

`analysis`는 이 결과를 YOLO callback payload로 감싼다.

YOLO callback payload 예시:

```json
{
  "request_id": "REQ_20260618_001",
  "job_id": "AI_JOB_REQ_20260618_001",
  "yolo_result": {
    "obstruction_ratio": 0.057,
    "confidence_score": 0.9404,
    "yolo_status": "good"
  }
}
```

## XGBoost 입력 feature 생성

`analysis`는 YOLO 결과와 백엔드 센서값을 합쳐 XGBoost 입력 feature를 만든다.

XGBoost 입력 feature 계약:

- `obstruction_ratio`: YOLO 결과
- `confidence_score`: YOLO 결과
- `water_level`: 정규화된 수위
- `flow_velocity`: 정규화된 유속

현재 feature batch 형태:

```python
{
    "obstruction_ratio": [obstruction_ratio],
    "confidence_score": [confidence_score],
    "water_level": [water_level],
    "flow_velocity": [flow_velocity],
}
```

## 센서값 정규화

현재 MVP 정규화 정책:

- `water_level = water_level_cm / 100.0`
- `flow_velocity = flow_velocity_mps / 1.0`
- 두 값 모두 `0.0` 이상 `1.0` 이하로 clamp

예시:

- `water_level_cm = 98.13` -> `water_level = 0.9813`
- `flow_velocity_mps = 0.4512` -> `flow_velocity = 0.4512`

이 정책은 실제 XGBoost 학습 feature scaling이 확정되면 다시 검토해야 한다. 실제 모델 담당자는 학습 시 사용한 feature scaling과 이 adapter의 정규화 정책이 일치하는지 반드시 확인해야 한다.

## XGBoost 단계 연결

현재 XGBoost 단계는 실제 학습 모델이 아니라 rule-based baseline을 사용한다.

`ai_service/xgboost/rule_baseline_predictor.py`

`analysis`는 XGBoost predictor가 아래 값을 반환한다고 가정한다.

- `risk_score`
- `risk_level`
- `final_decision`

XGBoost callback payload 예시:

```json
{
  "request_id": "REQ_20260618_001",
  "job_id": "AI_JOB_REQ_20260618_001",
  "xgboost_result": {
    "risk_score": 0.65,
    "risk_level": "caution",
    "final_decision": "monitoring",
    "evaluated_at": "2026-06-19T13:30:00+09:00"
  }
}
```

`evaluated_at`은 runtime에 `+09:00` offset을 가진 ISO 문자열로 생성된다.

## final_decision mapping

현재 XGBoost 내부 baseline은 `final_decision`을 `risk_level`과 같은 값으로 반환한다.

백엔드 callback contract에서는 별도의 최종 판단 코드가 필요하므로, `analysis` 계층에서 아래 mapping을 수행한다.

| risk_level | final_decision |
| --- | --- |
| `good` | `normal` |
| `caution` | `monitoring` |
| `danger` | `dispatch_required` |
| `unknown` | `field_check` |

실제 XGBoost 모델을 적용할 때도 백엔드 callback에 들어가는 `final_decision` 값은 이 contract와 맞아야 한다.

## 오류 정책

`analysis` 계층은 잘못된 입력에 대해 `ValueError`를 발생시킨다.

현재 오류 조건:

- top-level payload가 dict가 아님
- 필수 top-level key 누락: `request_id`, `drain_id`, `sensor_data`
- `sensor_data`가 dict가 아님
- 필수 sensor key 누락: `measured_at`, `water_level_cm`, `flow_velocity_mps`, `quality_status`
- `sensor_data.quality_status`가 `valid`가 아님

HTTP status code 변환은 `ai_service/http` 계층에서 처리한다.

## 예시 파일

정적 예시 파일:

- `ai_service/analysis/examples/request_payload.json`
- `ai_service/analysis/examples/orchestration_result.json`

이 파일들은 문서용 fixture이며 runtime에서 읽지 않는다.
