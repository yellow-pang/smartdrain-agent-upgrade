# XGBoost risk service

이 폴더가 현재 개발·고도화 담당 범위입니다.

## 핵심 흐름

```text
yolo_result_id
→ YOLO 결과 조회
→ 동일 drain_id의 captured_at 이전 센서 30분 이력 조회
→ 동일 drain_id의 최근 YOLO 이력 조회
→ 최신값·5분·30분 Feature 생성
→ 센서 품질 진단
→ 품질 게이트
→ XGBoost 3-class 예측
→ 상태 코드 해석
→ xgboost_data 저장
```

학습 클래스는 `good`, `caution`, `danger`입니다. `unknown`은 센서 누락, stale, 낮은 YOLO 신뢰도 등에서 품질 게이트가 반환합니다.

## 소스 패키지

Python 패키지명은 `flood_risk_xgb`입니다. 상위 폴더명이 `xgboost`이므로 설치된 XGBoost 라이브러리와의 이름 충돌을 피하기 위해 src-layout을 사용합니다.

## 주요 모듈

| 경로 | 역할 |
|---|---|
| `features/builder.py` | 센서·YOLO 이력 기반 고정 길이 Feature 생성 |
| `policy/sensor_diagnostics.py` | sensor spike/stuck/stale/no-valid 검사 |
| `policy/quality_gate.py` | 모델 실행 가능 여부 판단 |
| `policy/state_interpreter.py` | 상태 코드와 reason code 해석 |
| `policy/decision.py` | 최종 대응 코드 결정 |
| `inference/predictor.py` | XGBoost 모델 로딩·Feature 계약 검증·추론 |
| `repositories/jsonl.py` | DB 대체 JSONL 저장소 |
| `service.py` | 전체 분석 오케스트레이션 |

## 모델

- `models/xgb_mock_baseline.json`: 합성 데이터 기반 개발용 모델
- `models/model_metadata.json`: Feature 순서, 클래스 매핑, 모델 버전
- `models/evaluation.json`: 합성 holdout 평가 결과

현재 모델 버전은 `xgb-mock-v2.0.0`입니다. 실제 현장 성능 근거가 아니라 파이프라인 검증용입니다.
