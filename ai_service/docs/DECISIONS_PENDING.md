# Pending team decisions

백엔드·DB 연동 전에 아래 항목을 팀에서 확정해야 한다. 괄호 안은 XGBoost 쪽 권장안이다.

## 1. DB 계약 우선 결정

1. 결과 테이블명
   - 권장: `xgboost_data`
   - 이유: 루트 ERD, 요구사항, API 흐름이 `xgboost_data` 기준이다.

2. 이미지 경로 컬럼명
   - 권장: DB/API는 `image_url`, XGBoost 내부 모델은 `image_uri` alias 매핑
   - 이유: 루트 ERD와 화면 문서는 `image_url` 기준이고, 현재 XGBoost는 `image_url` 입력을 이미 허용한다.

3. `unknown` 결과의 nullable 정책
   - 권장: `risk_score`, `sensor_measured_at` nullable 허용
   - 이유: 센서 누락, stale, 품질 게이트 실패 시 의미 있는 모델 확률이나 대표 센서 시각이 없을 수 있다.

4. 운영 해석 필드 저장 위치
   - 권장: `state_code`, `analysis_status`, `data_quality`, `reason_codes`는 최소 `xgboost_data` 또는 결과 조회 DTO에 포함
   - 이유: 프론트/운영자가 위험도뿐 아니라 판단 사유와 품질 상태를 확인해야 한다.

5. trace 저장 방식
   - 권장: 별도 trace 테이블 또는 JSON 컬럼
   - 후보 필드: `feature_values_json`, `class_probabilities_json`, `source_refs_json`, `decision_reason`, `sensor_window_start`, `sensor_window_end`, `xgboost_model_version`

## 2. 실행 방식 결정

6. XGBoost 실행 트리거
   - 후보: API 호출, DB polling, 메시지 큐, 배치
   - MVP 권장: 백엔드가 `yolo_result_id`를 넘겨 분석을 호출하는 방식

7. 같은 YOLO 결과 재분석 허용 정책
   - 권장: 기본 중복 방지, `force=true` 같은 명시 옵션으로만 재분석 허용

8. YOLO 이력 Feature 처리
   - 후보:
     1. `yolo_result_data`에 `analysis_target` 또는 처리 상태 컬럼 추가
     2. 현재 분석 대상 `yolo_result_id`만 트리거하고 같은 테이블에서 과거 이력을 조회
     3. 초기 운영에서는 YOLO 이력 Feature 제외

## 3. 데이터 품질·모델 운영 결정

9. 센서 lookback 기본값
   - 현재 구현: 30분

10. 센서 수집 간격과 최소 유효 개수
    - 현재 구현은 품질 게이트에서 최소 유효 개수를 사용한다.

11. YOLO 모델 버전과 XGBoost 모델 버전의 DB 기록 방식
    - 권장: XGBoost 모델 버전은 trace에 저장하고, 필요 시 결과 테이블에도 최근 버전을 중복 저장한다.

12. `obstruction_ratio`의 정확한 의미
    - 결정 필요: 실제 막힘 면적 비율, blocked 확률, 별도 환산 점수 중 무엇인지
    - 현재 XGBoost 해석: 0에 가까울수록 막힘 징후 낮음, 1에 가까울수록 막힘 징후 높음

13. 실제 정답 라벨의 출처
    - 후보: 현장 출동, 관리자 판정, 민원, 침수 기록, 전문가 라벨
    - 현재 모델은 synthetic mock baseline이므로 운영 성능 근거로 사용하지 않는다.

## 4. 프론트·백엔드 표시 계약

14. 대시보드/상세 API 최소 필드
    - 권장:

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

15. `reason_codes` 표시 방식
    - 권장: DB에는 배열 JSON으로 저장하고, 프론트에서는 코드별 한글 문구 매핑을 별도로 둔다.
