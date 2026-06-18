# Project context for the XGBoost service

## 전체 프로젝트 목표

CCTV 스냅샷 또는 샘플 이미지와 수위·유속 센서 데이터를 결합해 개별 빗물받이의 침수 위험도를 판단하고, PostgreSQL에 저장한 결과를 백엔드와 프론트엔드가 활용하는 MVP이다.

```text
이미지
→ OpenCV / YOLO
→ yolo_result_data 저장

센서 수위·유속 시계열
→ sensor_data 저장

YOLO 결과 + 최근 YOLO 이력 + 센서 최신·과거 이력
→ XGBoost
→ report_data / xgboost_data 저장
→ Backend / WebSocket / Frontend
```

## 현재 담당 범위

현재 기여자는 XGBoost 영역만 담당한다.

포함:

- DB 형태의 YOLO 결과 조회
- 동일 `drain_id`와 기준 시각 이전의 센서 시계열 조회
- 최신값과 과거 추세 Feature 생성
- 최근 YOLO 막힘 추세 Feature 생성
- 데이터 품질 검사와 `unknown` 처리
- XGBoost 학습·추론·평가
- `state_code`, `reason_codes`, `data_quality`, `analysis_status` 산출
- 위험 결과 저장 형식 생성
- 목업 저장소와 향후 PostgreSQL 저장소의 경계 설계

제외:

- YOLO 재학습 및 모델 고도화
- OpenCV 전처리 고도화
- 센서 장비 연동
- FastAPI, WebSocket, 프론트엔드 구현
- DB DDL 소유권

## 위험 상태

| 화면 표시 | 내부 코드 |
|---|---|
| 양호 | `good` |
| 주의 | `caution` |
| 위험 | `danger` |
| 판단불가 | `unknown` |

`unknown`은 XGBoost의 학습 클래스가 아니라 입력 품질 문제를 나타내는 시스템 결과로 처리한다.

## 센서 사용 원칙

- 기준 시각은 YOLO 결과의 `captured_at`이다.
- 미래 센서값은 사용하지 않는다.
- 최신 유효 센서값과 최근 5분·30분 이력을 사용한다.
- `quality_status=valid`인 데이터만 Feature 계산에 사용한다.
- 센서값이 오래되거나 누락되면 `unknown`을 반환한다.
- 센서 spike/stuck/oscillation은 `data_quality=suspect`와 별도 상태 코드로 기록한다.
- YOLO 신뢰도가 낮더라도 센서가 명확한 고위험 상태라면 센서 기반 위험 판단을 허용한다.

## Mock-first 전략

DB가 준비되기 전에는 JSONL 파일이 테이블 역할을 한다.

```text
mock_data/fixtures/yolo_result_data.jsonl
mock_data/fixtures/sensor_data.jsonl
mock_data/runtime/xgboost_data.jsonl
```

향후 저장소 구현만 교체하고 Feature 생성과 예측 코드는 유지한다.
