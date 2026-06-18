# Data contract

## 1. YOLO 결과 입력

```json
{
  "yolo_result_id": 1,
  "drain_id": 101,
  "captured_at": "2026-06-18T14:30:00+09:00",
  "image_uri": "mock://drain_101/latest.jpg",
  "obstruction_ratio": 0.82,
  "confidence_score": 0.91,
  "yolo_status": "막힘",
  "analysis_target": true
}
```

XGBoost는 YOLO 모델 파일, 클래스명, 추론 코드에 직접 의존하지 않는다. `obstruction_ratio`는 모델 교체 후에도 다음 의미를 유지해야 한다.

```text
0에 가까움: 막힘 징후가 낮음
1에 가까움: 막힘 징후가 높음
```

`yolo_status`는 표시·로그용 참고값이다. XGBoost Feature는 기본적으로 `obstruction_ratio`, `confidence_score`, 최근 YOLO 이력에서 계산한 집계값을 사용한다.

`analysis_target=false`인 YOLO 행은 현재 분석 대상이 아니라 최근 이력 Feature 생성을 위한 과거 행이다. 실제 DB에서는 별도 컬럼을 두거나, 실행 트리거가 현재 대상 행만 전달하는 방식으로 처리할 수 있다.

루트 ERD와 화면 문서는 이미지 경로 컬럼을 `image_url`로 정의한다. XGBoost 내부 모델은 `image_uri`를 표준 직렬화 이름으로 사용하지만, 입력에서는 `image_url`도 허용한다. DB 연동 시에는 다음 중 하나로 명확히 매핑해야 한다.

```text
DB: yolo_result_data.image_url -> XGBoost: YoloResult.image_uri
```

새 DB 컬럼을 정할 수 있다면 전체 백엔드/프론트 문서와 맞추기 위해 `image_url`을 유지하는 편이 안전하다.

## 2. 센서 입력

```json
{
  "measured_at": "2026-06-18T14:29:00+09:00",
  "drain_id": 101,
  "water_level_cm": 74.8,
  "flow_velocity_mps": 0.28,
  "quality_status": "valid"
}
```

허용 품질 코드:

- `valid`: Feature에 사용
- `suspect`: 기록은 유지하지만 기본 Feature에서 제외
- `missing`: Feature에서 제외
- `invalid`: Feature에서 제외

센서 사용 원칙:

```text
sensor.measured_at <= yolo_result.captured_at
quality_status = valid인 값만 모델 Feature 계산에 사용
최근 5분과 30분 구간 집계 Feature 생성
미래 센서값 사용 금지
```

## 3. XGBoost 결과

```json
{
  "xgboost_id": 1,
  "drain_id": 101,
  "sensor_measured_at": "2026-06-18T14:30:00+09:00",
  "yolo_result_id": 1,
  "evaluated_at": "2026-06-18T05:31:00+00:00",
  "risk_score": 0.0183,
  "risk_level": "good",
  "final_decision": "normal",
  "analysis_status": "completed",
  "data_quality": "valid",
  "state_code": "NORMAL_DRAINAGE",
  "reason_codes": ["FLOW_VELOCITY_FAST"]
}
```

`risk_score`는 `danger` 클래스 확률이다. `unknown`은 모델 학습 클래스가 아니라 품질 게이트 결과이다.

`unknown`, `skipped`, `failed` 결과에서는 다음 값이 없을 수 있다.

```text
sensor_measured_at
risk_score
```

이 경우 임의 기본값을 저장하지 말고 `null`을 허용하는 것을 권장한다. 화면에서는 `risk_level=unknown`, `analysis_status`, `data_quality`, `state_code`, `reason_codes`를 함께 표시해야 한다.

## 4. 주요 코드 세트

### 위험 단계

```text
good
caution
danger
unknown
```

### 최종 대응

```text
normal
monitoring
field_check
dispatch_required
review_required
```

### 분석 상태

```text
completed
degraded
skipped
failed
```

### 데이터 품질

```text
valid
suspect
stale
insufficient
invalid
```

## 5. 분석 추적 정보

현재 ERD의 필드만으로는 여러 센서 이력과 YOLO 이력을 사용한 예측을 완전히 재현하기 어렵다. 따라서 목업에서는 별도 trace 파일에 다음 값을 남긴다.

- 센서 조회 시작·종료 시각
- 사용 Feature 스냅샷
- 클래스별 확률
- XGBoost 모델 버전
- 품질 경고
- 상태 코드
- 판단 사유
- reason code
- 원천 데이터 참조 수

실제 DB에서는 `feature_values_json`, `source_refs_json`, `decision_reason`, 센서 윈도우 컬럼, 상태 코드 컬럼 추가 여부를 백엔드 담당자와 확정해야 한다.

## 6. 백엔드·프론트 표시 최소 계약

대시보드와 상세 화면은 같은 위험도 기준을 사용해야 한다. API 응답은 최소 아래 값을 조합해서 제공해야 한다.

```text
drain_id
evaluated_at
risk_level
risk_score
final_decision
analysis_status
data_quality
state_code
reason_codes
yolo_result_id
sensor_measured_at
obstruction_ratio
confidence_score
water_level_cm
flow_velocity_mps
image_url
```

`xgboost_data`에 모든 값을 중복 저장할 필요는 없다. `obstruction_ratio`, `confidence_score`, `image_url`은 `yolo_result_data`에서, `water_level_cm`, `flow_velocity_mps`는 대표 센서 행 또는 최신 센서 조회에서 조인해 제공할 수 있다.

## 7. 현재 구현과 루트 기획의 관계

현재 XGBoost 구현은 루트 기획의 필수 입력인 `obstruction_ratio`, `confidence_score`, `water_level_cm`, `flow_velocity_mps`를 포함한다. 여기에 최근 5분/30분 센서 이력, 최근 YOLO 이력, 품질 진단 값을 추가로 사용한다. 이는 MVP 입력을 대체하는 것이 아니라, 같은 입력 계약을 기반으로 한 XGBoost 내부 Feature 확장이다.
