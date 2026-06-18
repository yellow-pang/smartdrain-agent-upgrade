# DB integration notes — team decisions required

## 문서 간 불일치 및 현재 내부 표준

| 항목 | 문서형 ERD 또는 논의 | 현재 코드 표준 |
|---|---|---|
| 결과 테이블 | `xgboost_data` 또는 `report_data` | 목업 파일명은 `xgboost_data.jsonl`, 의미는 `report_data` |
| 이미지 필드 | `image_url` 또는 `image_uri` | `image_uri` 우선, `image_url`도 입력 alias로 허용 |
| 위험 코드 | `양호/주의/위험` 또는 `good/caution/danger` | 내부/저장 표준은 `good/caution/danger/unknown` |
| 최종 판단 | `normal/monitoring/field_check/dispatch_required` | 여기에 `review_required` 추가 |
| 센서 이력 | 최신값 1건 또는 과거값 포함 | 최신값 + 최근 5분/30분 이력 사용 |

현재 코드의 내부 표준은 다음이다.

```text
risk_level: good | caution | danger | unknown
final_decision: normal | monitoring | field_check | dispatch_required | review_required
analysis_status: completed | degraded | skipped | failed
data_quality: valid | suspect | stale | insufficient | invalid
```

## 권장 DB 계약 표준안

백엔드와 DB 연동 전에는 아래를 기준으로 합의하는 것을 권장한다.

| 항목 | 권장안 | 이유 |
|---|---|---|
| 결과 테이블명 | `xgboost_data` 유지 | 루트 ERD와 요구사항 문서가 `xgboost_data`를 기준으로 정의되어 있다. |
| YOLO 이미지 컬럼 | DB 컬럼은 `image_url`, XGBoost 내부 모델은 `image_uri` 허용 | 루트 ERD·화면 문서는 `image_url` 기준이다. XGBoost는 `image_url`을 alias로 읽고 내부 직렬화는 `image_uri`를 사용한다. |
| `final_decision` 코드 | `normal`, `monitoring`, `field_check`, `dispatch_required`, `review_required` | 현재 XGBoost 공개 코드와 맞고, `unknown`/품질 재검토를 `review_required`로 표현할 수 있다. |
| `risk_score` 의미 | `danger` 클래스 확률 | 모델 출력 해석을 고정해 대시보드 점수와 trace 재현성을 맞춘다. |
| `unknown` 저장 | `risk_score`, `sensor_measured_at` nullable 허용 | 센서가 없거나 stale이면 의미 있는 대표 센서 시각과 모델 확률이 없을 수 있다. 임의값 저장보다 null이 안전하다. |
| 운영 해석 필드 | `state_code`, `analysis_status`, `data_quality`, `reason_codes`는 결과 조회에 포함 | 화면과 운영자가 "왜 위험/판단불가인지" 확인해야 하므로 최소 결과 응답에 필요하다. |
| 상세 trace | 별도 trace 테이블 또는 JSON 컬럼 | 30분 센서 이력, YOLO 이력, Feature 스냅샷은 단일 `sensor_measured_at`만으로 재현할 수 없다. |

### `xgboost_data` 권장 최소 컬럼

루트 ERD의 필드에 운영 해석 필드를 추가한다.

```text
xgboost_id
drain_id
sensor_measured_at        # nullable
yolo_result_id
evaluated_at
risk_score                # nullable
risk_level
final_decision
analysis_status
data_quality
state_code
reason_codes_json
```

### 분석 trace 권장 필드

운영 DB에서 예측 재현성과 디버깅을 보존하려면 별도 `xgboost_analysis_trace` 테이블 또는 JSON 컬럼을 둔다.

```text
xgboost_id
yolo_result_id
drain_id
sensor_window_start
sensor_window_end
xgboost_model_version
feature_values_json
class_probabilities_json
decision_reason
warnings_json
source_refs_json
```

trace는 대시보드 목록 조회에는 필요하지 않지만, 상세 분석 화면·운영 로그·모델 디버깅에 필요하다.

## 과거 센서 사용으로 인한 추가 결정

현재 XGBoost는 단일 센서 행이 아니라 최근 30분 구간을 사용한다. `sensor_measured_at` 하나는 최신 대표 센서 시각만 나타낸다.

권장 추가 컬럼 또는 별도 trace 테이블:

```text
sensor_window_start
sensor_window_end
xgboost_model_version
feature_values_json
class_probabilities_json
state_code
data_quality
analysis_status
reason_codes_json
decision_reason
source_refs_json
```

## YOLO 이력 Feature

목업에서는 `analysis_target=false`인 YOLO 행을 과거 이력으로 사용한다. 실제 DB에서는 다음 중 하나를 결정해야 한다.

1. `yolo_result_data`에 `analysis_target` 또는 처리 상태 컬럼 추가
2. 실행 트리거에서 현재 분석 대상 `yolo_result_id`만 전달하고, XGBoost가 같은 테이블에서 과거 이력을 조회
3. YOLO 이력 Feature는 초기 운영에서 제외하고 추후 추가

## unknown 저장 문제

센서가 완전히 누락되거나 stale인 경우 다음 값은 존재하지 않을 수 있다.

```text
sensor_measured_at
risk_score
```

팀은 다음 중 하나를 결정해야 한다.

1. `unknown`을 위해 nullable 허용
2. 별도 실패/분석 상태 테이블 사용
3. 마지막 알려진 센서 시각과 별도 품질 필드 저장

목업 구현은 의미 왜곡을 피하기 위해 `null`을 허용한다.

## Repository mapping 초안

PostgreSQL adapter는 현재 protocol을 그대로 구현한다.

| Repository | 읽기/쓰기 대상 | 핵심 조건 |
|---|---|---|
| `YoloResultRepository.get_by_id` | `yolo_result_data` | `yolo_result_id` 기준 현재 분석 대상 조회 |
| `YoloResultRepository.list_all` | `yolo_result_data` | 같은 `drain_id`의 최근 YOLO 이력 Feature 계산에 사용 |
| `SensorRepository.list_between` | `sensor_data` | `drain_id` 일치, `start_time <= measured_at <= captured_at`, 미래 센서값 금지 |
| `XgboostResultRepository.find_latest_by_yolo_result_id` | `xgboost_data` | 같은 YOLO 결과 중 최신 `evaluated_at` 조회 |
| `XgboostResultRepository.processed_yolo_result_ids` | `xgboost_data` | pending 분석 중복 실행 방지 |
| `XgboostResultRepository.save` | `xgboost_data` | 결과 저장 후 `xgboost_id` 반환 |
| `AnalysisTraceRepository.save` | trace 테이블 또는 JSON 컬럼 | Feature·확률·판단 사유 저장 |

## 화면/API 최소 제공 필드

프론트엔드 대시보드와 상세 화면은 최소 아래 값을 받을 수 있어야 한다.

```text
drain_id
yolo_result_id
evaluated_at
risk_level
risk_score
final_decision
analysis_status
data_quality
state_code
reason_codes
sensor_measured_at
obstruction_ratio
confidence_score
water_level_cm
flow_velocity_mps
image_url
```

`obstruction_ratio`, `confidence_score`, `water_level_cm`, `flow_velocity_mps`, `image_url`은 XGBoost 결과 단독 필드가 아니라 YOLO·센서 최신 입력과 조인해서 제공해도 된다.
