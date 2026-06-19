# YOLO Predictor 교체 가이드

`ai_service/_yolo`는 현재 실제 YOLO 구현이 아니다.

이 디렉터리는 백엔드-AI 서버 연동 흐름을 먼저 검증하기 위해 임시 fake YOLO predictor를 제공한다. 실제 이미지 분석, CCTV 연동, YOLO weight 로딩은 아직 구현되어 있지 않다.

## 현재 구현

현재 사용 중인 임시 구현:

`ai_service/_yolo/fake_yolo_predictor.py`

이 predictor는 `drain_id`를 입력받고, 미리 정해진 mock YOLO 결과를 반환한다.

현재 MVP mock drain ID:

- `1`
- `2`
- `3`
- `4`

알 수 없는 `drain_id`는 `unknown` 결과를 반환한다.

## 책임 경계

`_yolo` 모듈은 predictor-only 모듈이다.

해야 하는 일:

- 입력값을 받아 YOLO 결과 dict를 반환한다.
- 실제 모델 적용 후에는 이미지 또는 image source를 해석해 YOLO 추론을 수행한다.
- 아래 출력 계약을 유지한다.

하면 안 되는 일:

- 백엔드 HTTP 요청을 직접 받기
- 백엔드 callback 직접 전송
- FastAPI import
- backend URL 관리
- HTTP timeout/retry 처리
- XGBoost 직접 호출
- DB 저장

YOLO 결과를 callback payload로 감싸는 일은 `ai_service/analysis`가 담당한다. callback 전송은 `ai_service/http`가 담당한다.

## 출력 계약

실제 YOLO 모델로 교체하더라도 반환 dict에는 아래 필드가 있어야 한다.

| 필드 | 의미 |
| --- | --- |
| `obstruction_ratio` | 막힘 비율 |
| `confidence_score` | YOLO 추론 신뢰도 |
| `yolo_status` | YOLO 상태 코드 |

예시:

```json
{
  "obstruction_ratio": 0.061,
  "confidence_score": 0.8504,
  "yolo_status": "good"
}
```

허용 `yolo_status`:

- `good`
- `dirty`
- `blocked`
- `unknown`

`unknown`은 지원하지 않는 drain ID, 이미지 없음, 추론 실패, 신뢰도 부족 등 상태 판단이 어려운 경우의 fallback으로 사용할 수 있다.

## 현재 mock 값

| drain_id | obstruction_ratio | confidence_score | yolo_status |
| ---: | ---: | ---: | --- |
| 1 | 0.0227 | 0.676 | good |
| 2 | 0.057 | 0.9404 | good |
| 3 | 0.002 | 0.9371 | good |
| 4 | 0.061 | 0.8504 | good |

알 수 없는 `drain_id` 반환 예시:

```json
{
  "obstruction_ratio": 0.0,
  "confidence_score": 0.0,
  "yolo_status": "unknown"
}
```

## 실제 YOLO 적용 시 교체 지점

우선 교체 대상:

- `ai_service/_yolo/fake_yolo_predictor.py`

필요하면 class 이름이나 내부 구현은 바꿀 수 있지만, `analysis` 계층이 받는 반환 dict 계약은 유지해야 한다.

실제 모델 담당자가 확인해야 할 것:

- `drain_id`만으로 image source를 찾을지, 별도 image URL을 받을지 결정
- CCTV/snapshot 연동 위치
- image preprocessing 위치
- YOLO weight 또는 model artifact 로딩 위치
- 추론 실패 시 `unknown` 처리 기준
- confidence threshold 기준
- `obstruction_ratio` 산출 방식

중요: 위 항목을 구현하더라도 `_yolo`에서 callback을 직접 보내면 안 된다. `_yolo`는 결과 dict만 반환해야 한다.
