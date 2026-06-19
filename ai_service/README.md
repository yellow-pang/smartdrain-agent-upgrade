# SmartDrain AI Service

이 디렉터리는 SmartDrain 백엔드와 AI 서버 사이의 비동기 분석 흐름을 담당한다.

현재 `ai_service`는 실제 YOLO/XGBoost 모델 학습 또는 완성된 모델 추론 서버가 아니다. 지금 구현된 목적은 백엔드가 AI 서버를 호출하고, AI 서버가 YOLO 단계와 XGBoost 단계를 거쳐 callback payload를 만들어 백엔드로 돌려보내는 연동 구조를 고정하는 것이다.

## 현재 역할

`ai_service`가 현재 담당하는 흐름은 다음과 같다.

1. 백엔드에서 분석 요청을 받는다.
2. 요청 payload를 검증한다.
3. `drain_id` 기준으로 YOLO 단계를 호출한다.
4. YOLO 결과와 센서값을 조합해 XGBoost 입력 feature로 변환한다.
5. XGBoost 단계를 호출한다.
6. YOLO/XGBoost 결과를 백엔드 callback payload로 구성한다.
7. 백엔드 callback endpoint로 결과를 전송한다.

전체 비동기 연동 계약은 아래 endpoint를 기준으로 한다.

- Backend -> AI: `POST /ai/analysis/run`
- AI -> Backend: `POST /api/ai-callback/yolo-result`
- AI -> Backend: `POST /api/ai-callback/xgboost-result`

센서값만 직접 넣는 동기 endpoint 형태인 `/ai/xgboost/predict`는 현재 이 패키지의 기준 계약이 아니다.

## 현재 구현 상태

구현되어 있는 것:

- FastAPI 기반 `POST /ai/analysis/run` endpoint skeleton
- 백엔드 요청 payload 검증
- accepted response 생성
- 임시 fake YOLO predictor 호출
- YOLO 결과를 XGBoost 입력 feature로 변환
- 임시 rule-based XGBoost baseline 호출
- YOLO callback payload 생성
- XGBoost callback payload 생성
- best-effort 방식의 백엔드 callback 전송
- 위 흐름에 대한 테스트

아직 구현되어 있지 않은 것:

- 실제 YOLO 모델 추론
- CCTV API 연동
- 이미지 다운로드 또는 이미지 전처리
- YOLO weight 로딩
- 실제 XGBoost 학습 모델 로딩
- XGBoost model artifact 적용
- AI 서버 자체 DB 저장
- WebSocket 처리

## 디렉터리 책임

각 모듈은 아래 책임 경계를 지켜야 한다.

| 경로 | 책임 |
| --- | --- |
| `ai_service/http` | HTTP endpoint, background task 등록, callback 전송, timeout, retry, HTTP 오류 매핑 |
| `ai_service/analysis` | 요청 검증, YOLO 호출, XGBoost 호출, feature 변환, callback-ready payload 생성 |
| `ai_service/_yolo` | YOLO predictor 역할만 수행. 입력을 받아 YOLO 결과 dict 반환 |
| `ai_service/xgboost` | XGBoost predictor 역할만 수행. feature batch를 받아 위험도 결과 dict 반환 |

중요한 규칙:

- `_yolo`는 백엔드 callback을 직접 보내면 안 된다.
- `xgboost`는 백엔드 callback을 직접 보내면 안 된다.
- `_yolo`와 `xgboost`는 FastAPI, backend URL, HTTP timeout/retry 정책을 알면 안 된다.
- HTTP 통신은 `ai_service/http` 계층만 담당한다.
- YOLO와 XGBoost 사이의 연결은 `ai_service/analysis` 계층이 담당한다.

## 실제 모델 담당자가 봐야 할 문서

실제 YOLO/XGBoost 모델을 학습하고 적용할 담당자는 아래 문서를 우선 확인하면 된다.

- `ai_service/_yolo/README.md`: fake YOLO를 실제 YOLO 추론으로 교체할 때 지켜야 할 출력 계약
- `ai_service/xgboost/README.md`: rule-based baseline을 실제 XGBoost 모델로 교체할 때 지켜야 할 입력/출력 계약
- `ai_service/analysis/README.md`: YOLO 결과가 XGBoost 입력으로 변환되는 위치와 sensor normalization 정책
- `ai_service/HTTP_API_DESIGN.md`: 백엔드와 AI 서버 사이의 HTTP 요청/응답/callback 계약

## 실행

AI 서버 실행:

```cmd
python -m uvicorn ai_service.http.app:app --host 0.0.0.0 --port 9000 --reload
```

로컬 테스트 환경 예시:

```cmd
python -m venv ai_service\.venv
ai_service\.venv\Scripts\activate.bat
python -m pip install pytest
python -m pip install -r ai_service\requirements.txt
python -m pytest ai_service
```

가상환경을 활성화하지 않고 실행하는 경우:

```cmd
ai_service\.venv\Scripts\python.exe -m pytest ai_service
```
