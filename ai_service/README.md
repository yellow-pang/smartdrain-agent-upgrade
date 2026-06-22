# SmartDrain AI Service

이 디렉터리는 SmartDrain 백엔드와 AI 서버 사이의 비동기 분석 흐름을 담당한다.

현재 `ai_service`는 학습된 YOLO/XGBoost artifact를 사용하는 분석 서버 골격이다. 백엔드가 AI 서버를 호출하면, AI 서버가 `drain_id`로 mock image source를 찾고 YOLO 단계와 XGBoost 단계를 거쳐 callback payload를 만들어 백엔드로 돌려보낸다.

## 현재 역할

`ai_service`가 현재 담당하는 흐름은 다음과 같다.

1. 백엔드에서 분석 요청을 받는다.
2. 요청 payload를 검증한다.
3. `drain_id` 기준으로 `image_source` mock provider에서 이미지 소스를 찾는다.
4. resolve된 `local_path`를 YOLO에 전달한다.
5. YOLO 결과와 센서값을 조합해 XGBoost 입력 feature로 변환한다.
6. XGBoost 단계를 호출한다.
7. YOLO/XGBoost 결과를 백엔드 callback payload로 구성한다.
8. 백엔드 callback endpoint로 결과를 전송한다.

전체 비동기 연동 계약은 아래 endpoint를 기준으로 한다.

- Backend -> AI: `POST /ai/analysis/run`
- AI -> Backend: `POST /api/ai-callback/yolo-result`
- AI -> Backend: `POST /api/ai-callback/xgboost-result`

센서값만 직접 넣는 동기 endpoint 형태인 `/ai/xgboost/predict`는 현재 이 패키지의 기준 계약이 아니다.

## 현재 구현 상태

구현되어 있는 것:

- FastAPI 기반 `POST /ai/analysis/run` endpoint
- 백엔드 요청 payload 검증
- accepted response 생성
- `drain_id` 기반 mock image source resolve
- 실제 YOLO analyzer 호출
- YOLO 결과를 XGBoost 입력 feature로 변환
- 실제 XGBoost model artifact 기반 predictor 호출
- YOLO callback payload 생성
- XGBoost callback payload 생성
- best-effort 방식의 백엔드 callback 전송
- 위 흐름에 대한 테스트

아직 구현되어 있지 않은 것:

- CCTV API 연동
- 원격 이미지 다운로드
- AI 서버 자체 DB 저장
- WebSocket 처리

현재 production flow는 `ai_service/yolo/analyzer.py`와 `ai_service/xgboost/model_predictor.py`를 사용한다. `ai_service/yolo_legacy_example`와 `ai_service/xgboost/rule_baseline_predictor.py`는 legacy/reference 코드로 남겨둔다.

## 디렉터리 책임

각 모듈은 아래 책임 경계를 지켜야 한다.

| 경로 | 책임 |
| --- | --- |
| `ai_service/http` | HTTP endpoint, background task 등록, callback 전송, timeout, retry, HTTP 오류 매핑 |
| `ai_service/analysis` | 요청 검증, YOLO 호출, XGBoost 호출, feature 변환, callback-ready payload 생성 |
| `ai_service/image_source` | `drain_id` 기준 mock image source resolve. 현재 `source_url`과 `local_path`를 관리 |
| `ai_service/yolo` | YOLO predictor 역할만 수행. 입력을 받아 YOLO 결과 dict 반환 |
| `ai_service/xgboost` | XGBoost predictor 역할만 수행. feature batch를 받아 위험도 결과 dict 반환 |
| `ai_service/yolo_legacy_example` | 예전 fake YOLO predictor 참고/테스트용. production에서 사용하지 않음 |

중요한 규칙:

- `yolo`는 백엔드 callback을 직접 보내면 안 된다.
- `xgboost`는 백엔드 callback을 직접 보내면 안 된다.
- `yolo`와 `xgboost`는 FastAPI, backend URL, HTTP timeout/retry 정책을 알면 안 된다.
- HTTP 통신은 `ai_service/http` 계층만 담당한다.
- YOLO와 XGBoost 사이의 연결은 `ai_service/analysis` 계층이 담당한다.

## 실제 모델 담당자가 봐야 할 문서

실제 YOLO/XGBoost 모델을 학습하고 적용할 담당자는 아래 문서를 우선 확인하면 된다.

- `ai_service/yolo/README.md`: 실제 YOLO 추론에서 지켜야 할 출력 계약
- `ai_service/xgboost/README.md`: 실제 XGBoost 모델에서 지켜야 할 입력/출력 계약
- `ai_service/analysis/README.md`: YOLO 결과가 XGBoost 입력으로 변환되는 위치와 sensor normalization 정책
- `ai_service/HTTP_API_DESIGN.md`: 백엔드와 AI 서버 사이의 HTTP 요청/응답/callback 계약
- `ai_service/docs/korean_service_guide.md`: 사람이 읽기 쉬운 한글 운영/구조 가이드

## 실행

Python 3.12 기반 venv 재생성 및 의존성 설치는 아래 문서를 우선 확인한다.

```text
ai_service/docs/runtime_setup.md
```

AI 서버 실행:

```cmd
python -m uvicorn ai_service.http.app:app --host 0.0.0.0 --port 9000 --reload
```

callback 없이 로컬 모델 흐름만 확인하는 smoke test:

```cmd
python -m ai_service.scripts.smoke_analysis --drain-id 2
```

이 스크립트는 `image_source` resolve 결과를 출력하고, `local_path` 이미지 파일이 있을 때만 YOLO/XGBoost 분석을 실행한다. 백엔드 callback은 보내지 않는다.

로컬 테스트 환경 예시:

```cmd
python -m venv ai_service\.venv
ai_service\.venv\Scripts\activate.bat
python -m pip install pytest
python -m pip install -r ai_service\requirements.txt
python -m pytest ai_service
```

현재 실제 inference 실행에는 `numpy`, `opencv-python`, `ultralytics`, `pandas`, `xgboost`가 필요하다. `pytest`는 로컬 검증용 의존성이다.

가상환경을 활성화하지 않고 실행하는 경우:

```cmd
ai_service\.venv\Scripts\python.exe -m pytest ai_service
```

## Sample Image Check

실제 YOLO smoke test를 실행하려면 mock image source가 가리키는 샘플 이미지가 필요하다. 파일은 직접 생성하지 않으며, 사용자가 아래 경로에 배치한다.

```text
ai_service/samples/drain_1.jpg
ai_service/samples/drain_2.jpg
ai_service/samples/drain_3.jpg
ai_service/samples/drain_4.jpg
ai_service/samples/drain_5.jpg
```

배치 상태 확인:

```cmd
python -m ai_service.scripts.check_samples
```

이 명령은 YOLO 모델을 로드하지 않고 backend callback도 보내지 않는다.

## Pre-Commit Checklist

커밋 전 최종 점검은 아래 문서를 기준으로 한다.

```text
ai_service/docs/pre_commit_checklist.md
```
