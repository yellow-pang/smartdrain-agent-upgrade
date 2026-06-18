# Shared contracts

이 폴더는 YOLO, XGBoost, 백엔드가 공유해야 하는 DB-shaped 데이터 계약을 JSON Schema 형태로 둡니다.

현재 주요 계약은 다음입니다.

- `yolo_result.schema.json`
- `sensor_record.schema.json`
- `xgboost_result.schema.json`

주의사항:

1. XGBoost는 YOLO 모델 클래스명이나 `best.pt`에 직접 의존하지 않습니다.
2. XGBoost는 `obstruction_ratio`, `confidence_score`, `drain_id`, `captured_at` 중심으로 동작합니다.
3. 센서 입력은 `captured_at` 이전 데이터만 사용할 수 있습니다.
4. `state_code`, `analysis_status`, `data_quality`, `reason_codes`는 단순 모델 클래스보다 더 자세한 운영 해석을 제공하기 위한 확장 필드입니다.
5. 실제 DB DDL이 확정되면 이 JSON Schema와 repository adapter를 함께 조정해야 합니다.
