# SmartDrain AI Service 한글 가이드

이 문서는 `ai_service`를 처음 보는 사람이 현재 구조와 실행 흐름을 빠르게 이해하기 위한 운영/구조 가이드다.

## 현재 전체 흐름

백엔드는 AI 서버에 `POST /ai/analysis/run` 요청을 보낸다.

현재 backend request에는 `image_path`를 넣지 않는다. 백엔드는 아래 값만 보낸다.

- `request_id`
- `drain_id`
- `sensor_data`

AI 서버는 `drain_id`를 기준으로 `ai_service/image_source`의 mock provider에서 이미지 소스를 찾는다. 백엔드 연동 흐름에서는 보통 DB PK 정수 id가 전달되지만, AI 서버 직접 호출과 테스트를 위해 `DR-002` 같은 drain 코드도 허용한다. 찾은 이미지 소스의 `local_path`를 YOLO에 넘기고, YOLO 결과와 센서값을 조합해 XGBoost 최종 위험도 판단을 수행한다.

처리가 끝나면 AI 서버는 백엔드 callback endpoint로 결과를 보낸다.

- `POST /api/ai-callback/yolo-result`
- `POST /api/ai-callback/xgboost-result`

callback payload shape는 현재 유지한다.

## 폴더 구조와 역할

| 경로 | 역할 |
| --- | --- |
| `ai_service/http` | FastAPI endpoint, background task 등록, backend callback 전송, timeout/retry 관리 |
| `ai_service/analysis` | 요청 검증, image source resolve, YOLO/XGBoost 연결, callback-ready payload 생성 |
| `ai_service/image_source` | `drain_id` 기준 mock 이미지 소스 조회 |
| `ai_service/yolo` | 실제 YOLO/OpenCV 이미지 분석기 |
| `ai_service/xgboost` | 실제 XGBoost 모델 기반 위험도 predictor |
| `ai_service/model` | 학습된 모델 artifact 보관 |
| `ai_service/docs` | 운영/설계/실행 문서 |

## 모델 파일

현재 production flow에서 사용하는 모델 파일은 아래 위치에 있다.

- YOLO: `ai_service/model/best.pt`
- XGBoost: `ai_service/model/sewer_xgboost_model.json`

모델 학습은 이미 끝난 상태로 보고, `ai_service`에서는 학습이 아니라 추론과 callback 흐름만 담당한다.

## Backend POST 요청 예시

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

`image_path`는 보내지 않는다.

요청 단계에서 검증하는 값:

- `request_id`는 비어 있지 않은 문자열이어야 한다.
- `drain_id`는 정수 id 또는 `DR-###` 형식 drain 코드여야 한다.
- `sensor_data.measured_at`은 날짜와 시간이 포함된 ISO datetime 문자열이어야 한다.
- `sensor_data.water_level_cm`은 유한한 숫자여야 한다.
- `sensor_data.flow_velocity_mps`는 유한한 숫자여야 한다.
- `sensor_data.quality_status`는 `valid`여야 한다.

이 조건을 만족하지 않는 요청은 background task로 넘기지 않고 `400 Bad Request`로 거절한다.

## 내부 처리 순서

1. `ai_service/http`가 `POST /ai/analysis/run` 요청을 받는다.
2. `analysis.validator`가 payload를 검증한다.
3. `analysis.service`가 `drain_id`를 읽는다.
4. `image_source.service`가 `drain_id`에 해당하는 mock source를 찾는다.
5. mock source의 `local_path`를 YOLO analyzer에 넘긴다.
6. YOLO가 `obstruction_ratio`, `confidence_score`, `yolo_status`를 반환한다.
7. `analysis`가 YOLO 결과와 센서값을 XGBoost feature로 변환한다.
8. XGBoost가 `risk_score`, `risk_level`, `final_decision`을 반환한다.
9. `analysis`가 YOLO/XGBoost callback payload를 만든다.
10. `http`가 백엔드 callback endpoint로 payload를 전송한다.

## Image Source Mock 구조

현재 실제 CCTV 또는 스토리지 GET 연동은 없다. 대신 `drain_id` 1부터 5까지 mock source를 정의해 둔다.

각 source는 아래 값을 가진다.

- `source_url`: 미래 CCTV/스토리지 URL 자리
- `local_path`: 현재 YOLO가 읽는 mock 이미지 경로

예시:

```python
{
    "source_url": "mock://storage/drain-1-latest.jpg",
    "local_path": "mock_data/ai_image_samples/drain_1.jpg",
}
```

현재 `source_url`은 실제로 GET하지 않는다. 나중에 CCTV 또는 스토리지 연동이 준비되면 이 값을 실제 URL 또는 storage key로 바꿀 수 있다.

현재 `local_path`는 YOLO에 직접 전달된다. 실제 YOLO smoke test를 하려면 해당 경로에 이미지 파일이 있어야 한다.

## drain_id 1~5 Mock Source

| drain_id | source_url | local_path |
| ---: | --- | --- |
| 1 | `mock://storage/drain-1-latest.jpg` | `mock_data/ai_image_samples/drain_1.jpg` |
| 2 | `mock://storage/drain-2-latest.jpg` | `mock_data/ai_image_samples/drain_2.jpg` |
| 3 | `mock://storage/drain-3-latest.jpg` | `mock_data/ai_image_samples/drain_3.jpg` |
| 4 | `mock://storage/drain-4-latest.jpg` | `mock_data/ai_image_samples/drain_4.jpg` |
| 5 | `mock://storage/drain-5-latest.jpg` | `mock_data/ai_image_samples/drain_5.jpg` |

`drain_5.jpg`는 현재 의도적으로 없는 파일이다. CCTV 또는 외부 이미지 확보 실패 상황을 확인하기 위한 케이스이며, `check_samples`에서는 예상된 누락으로 처리한다.

## 없는 drain_id 정책

`image_source`에 등록되지 않은 `drain_id`가 들어오면 `ValueError`가 발생한다.

이 상태는 아래 중 하나로 본다.

- 등록되지 않은 drain ID
- CCTV 카메라 설정 이상
- 스토리지 이미지 소스 설정 이상

현재는 callback payload shape를 바꾸지 않는다. HTTP 요청 단계에서 image source 존재 여부를 확인하고, 등록되지 않은 `drain_id`는 `400 Bad Request`로 거절한다. background task 실행 중 실패하면 현재 구조에서는 실패 callback을 별도로 보내지 않는다.

추후 개선 방향은 둘 중 하나다.

- backend contract가 원하면 `400` 대신 `422`로 분리
- 백엔드와 별도 실패 callback contract를 합의한 뒤 failure callback 추가

## YOLO 역할

production YOLO 코드는 아래 파일을 사용한다.

```text
ai_service/yolo/analyzer.py
```

YOLO는 이미지를 분석해 아래 dict를 반환한다.

```json
{
  "obstruction_ratio": 0.057,
  "confidence_score": 0.9404,
  "yolo_status": "good"
}
```

정상 분석의 `obstruction_ratio`는 `0.0`부터 `1.0` 사이 값이어야 한다.

`yolo_status`가 `good`, `dirty`, `blocked`이면 `obstruction_ratio`와 `confidence_score`는 모두 `0.0` 이상 `1.0` 이하의 숫자여야 한다.

`yolo_status`가 `unknown`이면 `obstruction_ratio`와 `confidence_score`는 모두 `-1.0`이어야 한다. 문자열, `NaN`, `None`, dict 같은 값은 YOLO contract에서 거절한다.

이미지가 없거나 읽을 수 없거나 YOLO가 drain을 탐지하지 못하면 YOLO unknown 결과를 반환한다.

```json
{
  "obstruction_ratio": -1.0,
  "confidence_score": -1.0,
  "yolo_status": "unknown"
}
```

이 `-1.0` 값은 XGBoost가 YOLO 이상값 시나리오로 받아들이도록 `analysis` 계층에서 그대로 XGBoost feature에 전달한다.

## XGBoost 역할

production XGBoost 코드는 아래 파일을 사용한다.

```text
ai_service/xgboost/model_predictor.py
```

입력 feature 순서는 아래 순서를 유지해야 한다.

1. `obstruction_ratio`
2. `confidence_score`
3. `water_level`
4. `flow_velocity`

XGBoost 결과는 `analysis`에서 backend callback contract에 맞게 정리된다.

## 로컬 실행 명령어

PowerShell 기준:

```powershell
cd C:\dev_work\team_pro_01\smartdrain
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
python -m pip install -r .\ai_service\requirements.txt
python -m uvicorn ai_service.http.app:app --host 0.0.0.0 --port 9000 --reload
```

venv가 깨져 있으면 `ai_service/docs/runtime_setup.md`의 Python 3.12 venv 재생성 절차를 따른다.

## 검증 명령어

문법 검증:

```powershell
python -m compileall ai_service
```

테스트:

```powershell
python -m pytest ai_service
```

현재 환경에 `pytest`가 없으면 먼저 의존성을 설치해야 한다.

```powershell
python -m pip install -r .\ai_service\requirements.txt
```

## 로컬 모델 Smoke Test

백엔드 callback을 보내지 않고 image source resolve와 YOLO/XGBoost 분석만 확인하려면 아래 명령을 사용한다.

```powershell
python -m ai_service.scripts.smoke_analysis --drain-id 2
```

이 스크립트는 먼저 `drain_id`에 해당하는 `source_url`과 `local_path`를 출력한다. `local_path` 파일이 없으면 실제 YOLO 분석을 실행하지 않고 종료한다. 실제 분석까지 확인하려면 예를 들어 `mock_data/ai_image_samples/drain_2.jpg` 위치에 mock CCTV 이미지가 있어야 한다.

이 smoke test는 백엔드 callback을 보내지 않는다. callback 전송 확인은 FastAPI 서버와 백엔드를 같이 띄운 상태에서 `/ai/analysis/run`으로 확인해야 한다.

## 샘플 이미지 점검

실제 YOLO smoke test를 실행하려면 mock image source가 가리키는 샘플 이미지가 필요하다. 이미지는 직접 생성하지 않고 사용자가 아래 경로에 배치한다.

```text
mock_data/ai_image_samples/drain_1.jpg
mock_data/ai_image_samples/drain_2.jpg
mock_data/ai_image_samples/drain_3.jpg
mock_data/ai_image_samples/drain_4.jpg
mock_data/ai_image_samples/drain_5.jpg
```

배치 여부는 아래 명령으로 확인한다.

```powershell
python -m ai_service.scripts.check_samples
```

이 명령은 YOLO 모델을 로드하지 않고 backend callback도 보내지 않는다. `image_source` mock provider가 참조하는 local_path 파일 존재 여부만 확인한다.

## 커밋 전 최종 점검

커밋 전에는 아래 체크리스트를 기준으로 contract, 모델 경로, 샘플 이미지, 검증 명령을 확인한다.

```text
ai_service/docs/pre_commit_checklist.md
```

## 실제 CCTV/스토리지 연동 시 바꿀 위치

실제 외부 이미지 GET 연동이 들어오면 우선 아래 구조를 유지한다.

- `http`: 백엔드 요청 수신과 callback 전송
- `image_source`: `drain_id`로 source URL 또는 storage key resolve
- future fetcher/client: source URL에서 이미지 GET 후 local temp path 저장
- `analysis`: 최종 `local_path`를 YOLO에 전달
- `yolo`: local image path만 받아 분석

즉, 백엔드 request contract와 callback contract를 불필요하게 바꾸지 않고 `image_source`와 fetcher/client 쪽을 확장하는 방향이 좋다.
