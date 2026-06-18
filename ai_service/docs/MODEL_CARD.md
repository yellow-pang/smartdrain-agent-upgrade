# Mock baseline model card

## 용도

이 모델은 XGBoost 파이프라인, 목업 저장소, Feature 생성, 상태 해석, 결과 저장 흐름을 검증하기 위한 개발용 baseline이다.

## 학습 데이터

- 실제 현장 데이터가 아닌 합성 데이터
- YOLO obstruction, confidence, 최근 YOLO 추세를 합성
- 수위, 유속, 센서 추세를 규칙 기반으로 생성
- `good`, `caution`, `danger` 3개 클래스 학습
- `unknown`은 품질 게이트에서 처리
- `state_code`는 별도 상태 해석 모듈에서 산출

## Feature 그룹

```text
YOLO 현재값
- obstruction_ratio
- confidence_score

YOLO 과거 이력
- obstruction_mean_30m
- obstruction_delta_30m
- obstruction_persistence_count_30m

센서 최신값
- water_level_latest
- flow_velocity_latest

센서 5분/30분 이력
- mean
- delta
- slope
- max/min
- std
- valid ratio
```

## 사용 금지

- 실제 침수 경보 운영
- 안전 관련 자동 의사결정
- 현장 성능 주장
- 모델 정확도를 실제 서비스 성능으로 발표

## 교체 조건

실제 센서 이력과 실제 정답 라벨이 확보되면 동일 Feature 계약을 검토한 뒤 재학습한다. YOLO 모델이 교체되면 `obstruction_ratio`와 `confidence_score` 분포가 달라질 수 있으므로 XGBoost 재평가가 필요하다.
