# XGBoost Predictor 교체 가이드

`ai_service/xgboost`는 현재 실제 학습된 XGBoost 모델이 아니다.

이 디렉터리는 백엔드-AI 서버 연동 흐름과 feature contract를 먼저 고정하기 위해 임시 rule-based baseline predictor를 제공한다. 실제 XGBoost 모델 로딩, 학습, model artifact 적용은 아직 구현되어 있지 않다.

현재 모델 버전 표기:

`xgb_stub_v0`

## 현재 구현

현재 사용 중인 임시 구현:

`ai_service/xgboost/rule_baseline_predictor.py`

외부에서 사용하는 entrypoint:

`ai_service.xgboost.service.predict_flood_risk_batch(input_dict_batch)`

현재 구현은 feature 값을 규칙으로 판정해 `good`, `caution`, `danger`, `unknown` 중 하나를 반환한다. 이는 실제 학습 모델이 아니라 MVP 계약 검증용 baseline이다.

## 책임 경계

`xgboost` 모듈은 predictor-only 모듈이다.

해야 하는 일:

- 정해진 feature batch를 입력받는다.
- 위험도 결과 dict list를 반환한다.
- 실제 모델 적용 후에도 입력/출력 계약을 유지한다.

하면 안 되는 일:

- 백엔드 HTTP 요청을 직접 받기
- 백엔드 callback 직접 전송
- FastAPI import
- backend URL 관리
- HTTP timeout/retry 처리
- YOLO 직접 호출
- DB 저장

YOLO 결과와 센서값을 조합해 XGBoost feature를 만드는 일은 `ai_service/analysis`가 담당한다. callback 전송은 `ai_service/http`가 담당한다.

## 입력 feature 계약

입력은 dict-of-list batch 형태다. 모든 list 길이는 같아야 한다.

```python
input_dict_batch = {
    "obstruction_ratio": [0.061],
    "confidence_score": [0.8504],
    "water_level": [0.85],
    "flow_velocity": [0.05],
}
```

필수 feature:

| feature | 출처 | 의미 |
| --- | --- | --- |
| `obstruction_ratio` | YOLO 결과 | 막힘 비율 |
| `confidence_score` | YOLO 결과 | YOLO 추론 신뢰도 |
| `water_level` | backend sensor 값 정규화 | 수위 feature |
| `flow_velocity` | backend sensor 값 정규화 | 유속 feature |

현재 feature 순서:

```python
FEATURE_COLUMNS = [
    "obstruction_ratio",
    "confidence_score",
    "water_level",
    "flow_velocity",
]
```

실제 XGBoost 모델을 적용할 때는 학습 시 사용한 feature 순서, scaling, 결측치 처리 기준이 이 계약과 일치해야 한다.

## 출력 계약

`predict_flood_risk_batch`는 `list[dict]`를 반환한다.

각 row 결과에는 최소 아래 필드가 필요하다.

- `risk_score`
- `risk_level`
- `final_decision`

현재 구현은 테스트와 디버깅을 위해 아래 필드도 포함한다.

- `index`
- `feature_snapshot`
- `model_version`

반환 예시:

```json
[
  {
    "index": 0,
    "risk_level": "danger",
    "risk_score": 0.85,
    "final_decision": "danger",
    "feature_snapshot": {
      "obstruction_ratio": 0.061,
      "confidence_score": 0.8504,
      "water_level": 0.85,
      "flow_velocity": 0.05
    },
    "model_version": "xgb_stub_v0"
  }
]
```

허용 `risk_level`:

- `good`
- `caution`
- `danger`
- `unknown`

현재 predictor 내부의 `final_decision`은 `risk_level`과 같은 값을 반환한다. 백엔드 callback에 들어가는 최종 decision code는 `ai_service/analysis` 계층에서 다시 mapping된다.

## 현재 unknown 처리

현재 rule-based baseline은 아래 경우 `unknown`을 반환한다.

- row 값 중 `None`이 있음
- row 값 중 `NaN`이 있음
- `confidence_score < 0.5`

실제 모델 적용 시에도 결측치, 낮은 YOLO confidence, feature 범위 초과에 대한 정책을 명확히 정해야 한다.

## 실제 XGBoost 적용 시 교체 지점

우선 교체 대상:

- `ai_service/xgboost/rule_baseline_predictor.py`

필요하면 함께 확인할 파일:

- `ai_service/xgboost/service.py`
- `ai_service/xgboost/constants.py`
- `ai_service/xgboost/validator.py`

실제 모델 담당자가 확인해야 할 것:

- model artifact 파일 형식
- model artifact 로딩 위치
- feature 순서
- feature scaling
- 결측치 처리
- confidence threshold 정책
- `risk_score` 산출 범위
- `risk_level` 기준
- backend callback용 `final_decision` mapping과의 관계

중요: 실제 모델을 적용하더라도 `xgboost` 모듈에서 callback을 직접 보내면 안 된다. 이 모듈은 feature batch를 받아 위험도 결과만 반환해야 한다.

## 테스트

저장소 루트에서 실행:

```bash
python -m pytest ai_service
```

현재 테스트는 입력 feature 계약, batch shape 검증, 기본 위험도 결과, unknown 처리 기준을 확인한다.
