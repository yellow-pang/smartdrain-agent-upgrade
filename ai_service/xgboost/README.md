# XGBoost Risk Service

이 폴더는 빗물받이 침수 위험을 판단하는 XGBoost 서비스 구현입니다. 실제 YOLO 코드는 포함하지 않으며, YOLO가 만들어 저장했다고 가정한 `yolo_result` 레코드와 센서 레코드를 입력으로 사용합니다.

## 한 줄 요약

```text
yolo_result + sensor_data → Feature 24개 → XGBoost 예측 → 위험도/상태/조치 코드 저장
```

## 입력

### YOLO 결과 레코드

XGBoost가 직접 이미지를 보거나 YOLO 모델을 실행하지 않습니다. 아래 값이 DB 또는 JSONL에 이미 저장되어 있다고 가정합니다.

```text
yolo_result_id
drain_id
captured_at
image_uri
obstruction_ratio
confidence_score
yolo_status
analysis_target
```

주요 Feature로 쓰이는 값은 `obstruction_ratio`, `confidence_score`, 최근 30분의 obstruction 이력입니다.

### 센서 레코드

```text
drain_id
measured_at
water_level_cm
flow_velocity_mps
quality_status
```

미래 데이터 누수를 막기 위해 `measured_at`이 `captured_at`보다 늦은 센서 값은 사용하지 않습니다.

## 출력

분석 결과는 `xgboost_data` 형태로 저장됩니다.

```json
{
  "risk_score": 0.991,
  "risk_level": "danger",
  "final_decision": "field_check",
  "analysis_status": "completed",
  "data_quality": "valid",
  "state_code": "INTERNAL_OR_DOWNSTREAM_OBSTRUCTION_SUSPECTED",
  "reason_codes": [
    "WATER_LEVEL_VERY_HIGH",
    "WATER_LEVEL_RISING_FAST",
    "FLOW_VELOCITY_LOW"
  ]
}
```

`risk_level`은 `good`, `caution`, `danger`, `unknown` 중 하나입니다. `unknown`은 XGBoost가 학습한 클래스가 아니라 입력 데이터 품질이 부족해서 예측을 보류한 결과입니다.

## 주요 파일

| 경로 | 역할 |
|---|---|
| `src/flood_risk_xgb/domain.py` | 입력/출력 도메인 모델 |
| `src/flood_risk_xgb/features/schema.py` | Feature 순서 정의 |
| `src/flood_risk_xgb/features/builder.py` | YOLO/센서 이력으로 Feature 생성 |
| `src/flood_risk_xgb/policy/quality_gate.py` | 예측 가능 여부 판단 |
| `src/flood_risk_xgb/policy/state_interpreter.py` | 상황 코드와 근거 코드 생성 |
| `src/flood_risk_xgb/policy/decision.py` | 최종 조치 코드 생성 |
| `src/flood_risk_xgb/inference/predictor.py` | 모델 로딩, metadata 검증, 예측 |
| `src/flood_risk_xgb/repositories/jsonl.py` | JSONL 목업 저장소 |
| `src/flood_risk_xgb/repositories/postgres.py` | PostgreSQL 저장소 예정 위치 |
| `src/flood_risk_xgb/service.py` | 전체 분석 흐름 조립 |
| `mock_data/fixtures/` | 입력 fixture |
| `mock_data/examples/` | 예상 결과와 예시 출력 |
| `mock_data/runtime/` | 실행 시 생성되는 결과 |
| `shared/contracts/` | JSON 계약 |
| `docs/` | XGBoost 전용 설계/계약 문서 |

## 실행

기존 `ai_service/.venv`를 쓸 때는 `ai_service` 루트에서 실행합니다.

```powershell
cd C:\dev_work\team_proj_01\smartdrain\ai_service
.\.venv\Scripts\Activate.ps1
python xgboost\scripts\verify_setup.py
python -m pytest
```

목업 분석 실행:

```powershell
python xgboost\scripts\reset_mock_runtime.py
python xgboost\scripts\run_pending_analysis.py
Get-Content xgboost\mock_data\runtime\xgboost_data.jsonl
```

새 가상환경을 `xgboost/.venv`에 만들고 싶으면:

```powershell
cd C:\dev_work\team_proj_01\smartdrain\ai_service\xgboost
.\scripts\setup_venv.ps1
.\.venv\Scripts\Activate.ps1
python scripts\verify_setup.py
```

## 18개 시나리오

`mock_data/fixtures/`에는 정상, 표면 막힘, 내부/하류 막힘 의심, 유입량 과다, 센서 이상, 오래된 센서, 유효 센서 없음 등 18개 상황이 들어 있습니다.

검증 기준은 `mock_data/examples/expected_outcomes.jsonl`에 있으며, 자세한 설명은 `docs/SCENARIO_MATRIX.md`에 있습니다.

## 주의

- YOLO 구현은 이 폴더의 책임이 아닙니다.
- `yolo_result`라는 이름은 입력 데이터 계약으로만 사용합니다.
- Feature 순서를 바꾸면 모델과 metadata를 같이 갱신해야 합니다.
- 현재 모델은 목업 기반 개발용 baseline입니다.
