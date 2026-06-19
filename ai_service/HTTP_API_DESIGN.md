# AI 서버 HTTP API 설계

이 문서는 SmartDrain 백엔드와 AI 서버 사이의 HTTP 연동 계약을 설명한다.

현재 AI 서버는 실제 YOLO/XGBoost 모델 완성본이 아니라, 백엔드와 AI 서버 사이의 비동기 분석 흐름을 검증하기 위한 FastAPI adapter와 callback sender를 제공한다.

## 책임 경계

HTTP 통신은 `ai_service/http` 계층만 담당한다.

| 계층 | 책임 |
| --- | --- |
| `http` | HTTP 요청 수신, background task 등록, callback 전송, timeout, retry, HTTP 오류 매핑 |
| `analysis` | 요청 검증, YOLO/XGBoost 호출, callback-ready payload 생성 |
| `_yolo` | YOLO 결과 dict 반환 |
| `xgboost` | 위험도 결과 dict 반환 |

`_yolo`, `xgboost`, `analysis` 계층은 backend URL을 알거나 callback을 직접 보내면 안 된다.

## Endpoint 흐름

Backend -> AI:

- `POST /ai/analysis/run`

AI -> Backend callback:

- `POST /api/ai-callback/yolo-result`
- `POST /api/ai-callback/xgboost-result`

기본 로컬 포트 기준:

- Backend: `http://localhost:8000`
- AI server: `http://localhost:9000`

AI 서버 실행 entrypoint:

`ai_service.http.app:app`

실행 예시:

```cmd
python -m uvicorn ai_service.http.app:app --host 0.0.0.0 --port 9000 --reload
```

## Backend -> AI 요청

분석 시작 endpoint:

- Method: `POST`
- Path: `/ai/analysis/run`
- 목적: 백엔드가 특정 빗물받이에 대한 최신 센서값을 AI 서버에 전달하고 비동기 분석을 요청한다.

요청 body 예시:

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

현재 AI 서버는 이 요청을 받은 뒤 즉시 accepted response를 반환하고, 실제 분석 및 callback 전송은 background task 흐름으로 처리한다.

accepted response 예시:

```json
{
  "accepted": true,
  "request_id": "REQ_20260618_001",
  "job_id": "AI_JOB_REQ_20260618_001",
  "status": "processing"
}
```

현재 job ID 정책:

`job_id = AI_JOB_{request_id}`

이 정책은 MVP용 결정이며, 이후 queue나 DB job table을 도입하면 변경될 수 있다.

## 내부 처리 흐름

`POST /ai/analysis/run`은 HTTP 입력을 받은 뒤 내부적으로 아래 함수를 사용한다.

`ai_service.analysis.service.run_analysis_job(payload)`

처리 순서:

1. 요청 payload를 검증한다.
2. accepted response를 만든다.
3. `drain_id` 기준으로 YOLO 단계를 호출한다.
4. YOLO 결과와 센서값을 XGBoost feature로 변환한다.
5. XGBoost 단계를 호출한다.
6. YOLO callback payload를 만든다.
7. XGBoost callback payload를 만든다.
8. HTTP 계층이 callback endpoint로 payload를 전송한다.

## YOLO callback 계약

AI 서버가 백엔드로 보내는 YOLO callback:

- Method: `POST`
- Path: `/api/ai-callback/yolo-result`
- 목적: YOLO 중간 분석 결과 전달

payload 예시:

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

YOLO 결과 필드:

- `obstruction_ratio`: 막힘 비율
- `confidence_score`: YOLO 추론 신뢰도
- `yolo_status`: YOLO 상태 코드

허용 상태:

- `good`
- `dirty`
- `blocked`
- `unknown`

현재 fake YOLO는 실제 이미지 분석을 하지 않는다. 실제 YOLO 모델 담당자는 위 출력 계약을 유지하면서 `_yolo` 내부 predictor를 교체해야 한다.

## XGBoost callback 계약

AI 서버가 백엔드로 보내는 XGBoost callback:

- Method: `POST`
- Path: `/api/ai-callback/xgboost-result`
- 목적: 최종 위험도 분석 결과 전달

payload 예시:

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

XGBoost 결과 필드:

- `risk_score`: 위험도 점수
- `risk_level`: 위험 등급
- `final_decision`: 백엔드/화면에서 사용할 최종 판단 코드
- `evaluated_at`: 평가 시각

허용 `risk_level`:

- `good`
- `caution`
- `danger`
- `unknown`

허용 `final_decision`:

- `normal`
- `monitoring`
- `field_check`
- `dispatch_required`

현재 XGBoost는 실제 학습 모델이 아니라 rule-based baseline이다. 실제 XGBoost 담당자는 입력/출력 계약을 유지하면서 predictor 내부를 교체해야 한다.

## Callback 전송 정책

현재 callback 전송은 MVP용 best-effort 정책이다.

- `/ai/analysis/run`에서 accepted response를 먼저 반환한다.
- callback 성공/실패는 이미 반환된 accepted response를 바꾸지 않는다.
- YOLO callback을 먼저 시도한다.
- YOLO callback이 실패해도 XGBoost callback은 시도한다.
- 각 callback에는 timeout을 적용한다.
- 현재 retry는 제한적으로만 수행한다.
- persistent retry queue나 callback 상태 DB 저장은 구현되어 있지 않다.

callback 전송 구현 위치:

`ai_service/http/callback_sender.py`

## 오류 처리

`analysis` 계층은 잘못된 payload에 대해 `ValueError`를 발생시킨다.

HTTP 계층은 이 오류를 `400 Bad Request` 형태로 변환한다.

실제 모델 교체 작업 중에도 YOLO/XGBoost 내부에서 HTTP 오류 응답을 직접 만들지 않아야 한다. HTTP 오류 매핑은 `ai_service/http` 계층의 책임이다.
