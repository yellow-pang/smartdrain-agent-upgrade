# AI Service HTTP 계층

`ai_service/http`는 SmartDrain AI 서버의 FastAPI adapter와 백엔드 callback 전송을 담당한다.

이 계층은 실제 YOLO/XGBoost 모델을 구현하는 곳이 아니다. HTTP 요청을 받고, `analysis` 계층에 작업을 넘기고, 생성된 callback payload를 백엔드로 전송하는 역할만 한다.

## 책임

`http` 계층이 담당하는 일:

- `POST /ai/analysis/run` 요청 수신
- 요청 payload를 `analysis` 계층 검증 로직에 전달
- accepted response 즉시 반환
- background task 등록
- YOLO callback 전송
- XGBoost callback 전송
- callback timeout/retry 처리
- HTTP 오류 응답 매핑

`http` 계층이 하지 않는 일:

- 실제 YOLO 추론
- CCTV API 호출 또는 스토리지 GET 직접 구현
- 이미지 처리
- 실제 XGBoost 모델 추론 구현
- XGBoost feature 생성
- DB 저장
- YOLO/XGBoost 입출력 계약 변경

YOLO와 XGBoost를 연결하는 분석 흐름은 `ai_service/analysis`가 담당한다.

현재 이미지 소스 선택은 `ai_service/image_source`가 담당한다. 추후 실제 CCTV/스토리지 GET 연동이 들어오더라도 HTTP endpoint contract와 callback payload shape는 유지한다.

## Endpoint

Backend -> AI:

- `POST /ai/analysis/run`

이 endpoint는 백엔드 분석 요청 payload를 받고, MVP용 deterministic job ID를 만든 뒤 background callback 처리를 예약한다. 응답은 즉시 반환된다.

즉시 응답 예시:

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

## Background callback 흐름

background task 처리 순서:

1. `run_analysis_job(payload)`를 실행한다.
2. YOLO callback payload를 `/api/ai-callback/yolo-result`로 전송한다.
3. XGBoost callback payload를 `/api/ai-callback/xgboost-result`로 전송한다.

callback endpoint:

- `POST /api/ai-callback/yolo-result`
- `POST /api/ai-callback/xgboost-result`

callback 전송은 MVP 기준 best-effort 정책이다.

- callback 성공/실패는 이미 반환된 accepted response를 바꾸지 않는다.
- YOLO callback이 실패해도 XGBoost callback은 시도한다.
- 각 callback에는 timeout을 적용한다.
- 기본 retry 횟수는 1회다.
- persistent retry queue는 구현되어 있지 않다.
- callback 상태를 AI 서버 DB에 저장하지 않는다.

## 환경변수

| 환경변수 | 기본값 | 설명 |
| --- | --- | --- |
| `BACKEND_BASE_URL` | `http://localhost:8000` | callback을 보낼 백엔드 base URL |
| `BACKEND_CALLBACK_TIMEOUT_SECONDS` | `10` | callback 요청 timeout |
| `BACKEND_CALLBACK_RETRY_COUNT` | `1` | callback 실패 시 retry 횟수 |

로컬 AI 서버 기본 포트:

- `9000`

실행 명령:

```cmd
python -m uvicorn ai_service.http.app:app --host 0.0.0.0 --port 9000 --reload
```

## 백엔드 연동 smoke test

백엔드가 `http://localhost:8000`에서 실행 중일 때 아래 절차로 확인한다.

1. 의존성 설치

```cmd
python -m pip install -r ai_service/requirements.txt
```

venv가 깨져 있거나 Python 경로를 찾지 못하면 `ai_service/docs/runtime_setup.md`의 Python 3.12 venv 재생성 절차를 따른다.

2. AI 서버 실행

```cmd
python -m uvicorn ai_service.http.app:app --host 0.0.0.0 --port 9000 --reload
```

3. AI 서버 endpoint로 백엔드 형태 요청 전송

요청:

`POST http://localhost:9000/ai/analysis/run`

request body:

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

AI 서버는 `drain_id`를 기준으로 `ai_service/image_source` mock provider에서 이미지 소스를 resolve한다. 현재 backend request에는 `image_path`를 포함하지 않는다.

등록되지 않은 `drain_id`는 등록되지 않은 drain 또는 CCTV/스토리지 이미지 소스 설정 이상으로 보고 `ValueError`가 발생한다. 현재 HTTP 요청 단계의 잘못된 입력은 `400 Bad Request`로 매핑된다.

기대 즉시 응답:

```json
{
  "accepted": true,
  "request_id": "REQ_20260618_001",
  "job_id": "AI_JOB_REQ_20260618_001",
  "status": "processing"
}
```

4. 백엔드에서 callback 수신 확인

백엔드 로그에서 아래 요청이 들어왔는지 확인한다.

- `POST /api/ai-callback/yolo-result`
- `POST /api/ai-callback/xgboost-result`

callback 전송은 FastAPI background task에서 실행된다. 따라서 callback 성공/실패는 `/ai/analysis/run`의 즉시 응답을 바꾸지 않는다.

## 모델 담당자 주의사항

실제 YOLO/XGBoost 모델을 적용하더라도 HTTP 계층의 책임은 유지해야 한다.

- YOLO 모델 코드는 `yolo`에서 결과 dict만 반환한다.
- XGBoost 모델 코드는 `xgboost`에서 위험도 결과만 반환한다.
- 모델 계층에서 backend callback을 직접 보내면 안 된다.
- 모델 계층에서 FastAPI endpoint를 직접 만들면 안 된다.
- callback URL, timeout, retry 정책은 `http` 계층에서만 관리한다.

실제 YOLO/XGBoost 모델 전환 이후에도 HTTP callback contract는 유지된다. `/ai/analysis/run`은 accepted response를 즉시 반환하고, background task가 YOLO callback과 XGBoost callback을 순서대로 전송한다.
