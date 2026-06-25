# Plan 02. 상태별 시나리오 기반 실시간 시뮬레이터 보강

## 1. 요청 배경과 해결 문제

- 사용자가 직접 준비한 사진을 상태별로 넣어두면, 백엔드가 시연용 센서 데이터와 분석 결과를 자동으로 DB에 저장하는 구조가 필요하다.
- 목표 상태는 `양호`, `주의`, `위험`, `판단불가` 네 가지이며, 기존 대시보드와 상세 화면이 이 데이터를 그대로 조회하고 실시간으로 갱신할 수 있어야 한다.
- 실제 AI 모델이나 외부 AI Service 준비 여부와 무관하게, MVP 시연용 흐름이 반복 가능해야 한다.

## 2. 현재 구현 상태와 확인 근거

| 항목 | 현재 상태 | 확인 근거 |
| --- | --- | --- |
| 자동 시뮬레이터 | 주기적으로 drain별 `sensor_data`를 생성하고 기존 AI 분석 요청을 호출 | `backend/app/services/realtime_simulator.py` |
| 이미지 정적 제공 | `mock_data/ai_image_samples`를 `/api/mock-images`로 mount | `backend/app/main.py` |
| seed 이미지 매핑 | `drain_{id}.jpg`가 있을 때만 YOLO 결과의 `image_url`에 연결 | `backend/app/seeds/seed_mock_data.py`, `backend/app/services/analysis_async_service.py` |
| 위험 상태 값 | `good`, `caution`, `danger`, `unknown`을 사용 | `backend/app/services/dashboard_service.py`, `backend/app/services/analysis_async_service.py` |
| DB schema | 센서, YOLO, XGBoost 결과를 저장할 기존 테이블이 있음 | `backend/app/models/sensor_data.py`, `backend/app/models/yolo_result.py`, `backend/app/models/xgboost_result.py` |

## 3. 작업 범위 / 제외 범위

### 작업 범위

- 기존 `realtime_simulator`에 상태별 시나리오 생성 정책을 추가한다.
- 시뮬레이터 tick마다 drain별 상태를 무작위로 선택하고, 상태에 맞는 센서값/YOLO 결과/XGBoost 결과를 DB에 저장한다.
- 상태별 이미지 폴더 경로를 정하고, 해당 폴더에 있는 이미지 중 하나를 무작위로 `image_url`에 연결한다.
- 기존 대시보드/WebSocket 흐름이 갱신되도록 `DRAIN_STATUS_UPDATED`, 필요 시 YOLO/XGBoost 이벤트를 발행한다.
- backend README와 steps 문서에 사용자가 사진을 넣을 경로와 실행 방법을 기록한다.

### 제외 범위

- DB schema 및 Alembic migration 변경
- 실제 AI 모델 로직 또는 AI Service HTTP 계약 변경
- 프론트 화면 구조 변경
- Docker, Nginx, CI/CD 설정 변경
- 새 패키지 추가

## 4. 추천 구현 방향과 선택 이유

### 옵션 A. 기존 AI Service 요청 흐름을 유지하고 callback을 기다림

- 장점: 실제 AI 연동 경로와 유사하다.
- 단점: mock/실제 AI 서버가 없으면 시나리오가 끝까지 저장되지 않고, 사용자가 원하는 "사진만 넣으면 돌아가는 시연"과 거리가 있다.

### 옵션 B. realtime simulator가 시연용 분석 결과까지 직접 저장 (추천)

- 장점: 외부 AI 서버 없이도 `sensor_data`, `yolo_results`, `xgboost_results`, drain 상태가 한 번에 갱신된다.
- 장점: 기존 DB schema를 그대로 사용하므로 migration이 필요 없다.
- 장점: 상태별 이미지 폴더만 준비하면 대시보드가 즉시 mock 이미지 URL을 받을 수 있다.
- 단점: 실제 AI 분석 결과가 아니라 시연용 synthetic 결과임을 문서와 코드명으로 분명히 해야 한다.

### 추천 이유

- 이번 요청은 실제 모델 정확도보다 시나리오 재현성과 시연 안정성이 핵심이다.
- 기존 `realtime_simulator`가 이미 런타임 start/stop/status를 제공하므로, 이 계층 안에서 시연용 결과 저장까지 처리하는 것이 변경 범위가 작다.

## 5. 사진 배치 경로

사용자는 아래 폴더에 이미지를 넣는다.

```text
mock_data/ai_image_samples/scenarios/good/
mock_data/ai_image_samples/scenarios/caution/
mock_data/ai_image_samples/scenarios/danger/
mock_data/ai_image_samples/scenarios/unknown/
```

- `unknown`은 화면/DB의 기존 상태값과 맞춘 `판단불가` 시나리오다.
- 지원 확장자는 구현 시 `.jpg`, `.jpeg`, `.png`, `.webp` 범위로 제한한다.
- 폴더에 이미지가 없으면 해당 상태의 `image_url`은 `None`으로 저장하되, 센서/분석 결과 저장은 계속 진행한다.

## 6. 예상 변경 파일

| 경로 | 변경 내용 |
| --- | --- |
| `backend/app/services/realtime_simulator.py` | 상태별 시나리오 정의, 센서/YOLO/XGBoost 결과 직접 저장, 이미지 선택, WebSocket 이벤트 발행 |
| `backend/README.md` | 상태별 이미지 경로와 자동 시뮬레이터 사용법 보강 |
| `docs/steps/step-02-scenario-based-realtime-simulator.md` | 구현 완료 후 실제 변경/검증 기록 |

## 7. 단계별 작업 계획

1. 상태별 시나리오 프로필 정의
- `good`, `caution`, `danger`, `unknown`별 센서값 범위, 막힘률, 신뢰도, 최종 판단 문구를 정의한다.

2. 이미지 선택 유틸 추가
- `mock_data/ai_image_samples/scenarios/<risk_level>/`에서 이미지 파일을 무작위로 고르고 `/api/mock-images/scenarios/<risk_level>/<파일명>` URL로 변환한다.

3. 시뮬레이터 저장 흐름 변경
- tick마다 drain별로 시나리오를 무작위 선택한다.
- `SensorData`, `YoloResult`, `XgboostResult`를 하나의 DB 흐름으로 저장하고 `Drain.status`를 갱신한다.
- 외부 AI Service 요청은 이 시나리오 모드에서 호출하지 않는다.

4. WebSocket 이벤트 연결
- 저장한 결과를 기존 대시보드 이벤트 payload로 발행해 프론트가 기존 실시간 동기화 흐름을 사용할 수 있게 한다.

5. 문서와 검증 정리
- README에 이미지 경로와 상태 매핑을 적는다.
- backend import/compile 검증 및 가능한 API smoke를 실행한다.
- steps 문서에 실제 변경 내용과 검증 결과를 기록한다.

## 8. 예상 영향과 위험 요소

- 자동 시뮬레이터가 AI Service를 호출하지 않게 되므로, `analysis_jobs` 생성 흐름과는 분리된다.
- 실제 AI callback 통합 검증과 시연용 synthetic 결과 검증은 성격이 다르므로 문서에 구분해 적어야 한다.
- 이미지 파일명이 URL에 그대로 들어가므로 공백이나 특수문자가 많은 파일명은 브라우저 표시 문제가 날 수 있다. 가능하면 영문/숫자/하이픈 파일명을 권장한다.
- 폴더에 사진이 없어도 기능은 돌아가지만 화면에는 이미지가 비어 보일 수 있다.

## 9. 검증 방법

- `python -m compileall app` 또는 import 가능한 범위의 Python 문법 검증
- `GET /api/realtime-simulator/status`
- `POST /api/realtime-simulator/start`
- `GET /api/drains`, `GET /api/drains/{drainCode}/sensor-data`, `GET /api/drains/{drainCode}/risk-history`로 DB 저장 결과 확인
- 이미지 파일을 넣은 뒤 `/api/mock-images/scenarios/<risk_level>/<file>` 정적 URL 응답 확인

## 10. 사용자 승인이 필요한 결정 사항

1. 시나리오 모드에서 외부 AI Service 요청을 생략하고, backend가 시연용 분석 결과를 직접 저장해도 되는지 승인 필요
2. `판단불가`의 DB/API 상태값을 기존 체계에 맞춰 `unknown`으로 유지할지 승인 필요
3. 사진 경로를 `mock_data/ai_image_samples/scenarios/{good,caution,danger,unknown}/`로 확정할지 승인 필요

승인 후 위 범위 안에서 구현, 검증, steps 문서 작성까지 진행한다.
