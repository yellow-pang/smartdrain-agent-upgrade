# AI Service — XGBoost 중심 개발 스캐폴드 v2

이 저장소는 팀 프로젝트의 AI 영역을 `ai_service/` 아래에 분리한 구조입니다.

```text
ai_service/
├─ yolo/       # 다른 팀원 담당, 기존 PoC YOLO 모델을 임시 사용
├─ xgboost/    # 현재 개발·고도화 담당 범위
├─ shared/     # DB-shaped 데이터 계약
├─ mock_data/  # DB가 없을 때 사용하는 JSONL 목업 테이블
└─ scripts/    # 실행, 검증, 목업 생성 스크립트
```

핵심 원칙은 다음입니다.

```text
YOLO는 결과를 저장한다.
XGBoost는 YOLO 코드를 import하지 않고 저장된 결과만 읽는다.
XGBoost는 동일 drain_id의 최신·과거 센서 데이터를 결합해 위험도를 산출한다.
결과는 report_data/xgboost_data 형태로 저장한다.
```

현재는 PostgreSQL이 준비되지 않았으므로 JSONL 파일을 DB 테이블처럼 사용합니다.

```text
yolo_result_data.jsonl
+
sensor_data.jsonl
↓
센서 최신값 + 5분/30분 이력 + 최근 YOLO 이력 Feature
↓
XGBoost 3-class 위험도 분석
↓
xgboost_data.jsonl + analysis_trace.jsonl
```

## 1. 이번 버전 반영 사항

업로드된 기존 폴더를 기준으로 다음을 추가 반영했습니다.

- `ai_service/yolo`, `ai_service/xgboost` 분리 유지
- XGBoost가 YOLO 모델 파일과 추론 코드에 직접 의존하지 않도록 유지
- YOLO 현재값뿐 아니라 최근 YOLO 이력 Feature 추가
- 센서 최신값과 과거값 기반 Feature 확장
- 수위·유속 평균, 변화량, 기울기, 표준편차, 유효 데이터 비율 추가
- 센서 이상 탐지 추가
  - 수위 spike
  - 유속 센서 stuck
  - 센서 oscillation
  - stale sensor
  - no valid sensor
- `risk_level`과 별도로 `state_code`, `analysis_status`, `data_quality`, `reason_codes` 추가
- `final_decision`을 `normal`, `monitoring`, `field_check`, `dispatch_required`, `review_required`로 정리
- 목업 시나리오 18개로 확장
- 새 개발 세션용 `START_PROMPT.md` 추가

## 2. 빠른 시작

### Windows PowerShell

```powershell
cd ai_service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements\dev.txt
python -m pip install -e .
Copy-Item .env.example .env
python scripts\verify_setup.py
python scripts\run_pending_analysis.py
```

### macOS / Linux

```bash
cd ai_service
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements/dev.txt
python -m pip install -e .
cp .env.example .env
python scripts/verify_setup.py
python scripts/run_pending_analysis.py
```

분석 결과는 다음 파일에 생성됩니다.

```text
mock_data/runtime/xgboost_data.jsonl
mock_data/runtime/analysis_trace.jsonl
```

## 3. 주요 명령

```bash
# 특정 YOLO 결과 한 건 분석
python scripts/run_analysis.py --yolo-result-id 1

# 아직 처리되지 않은 YOLO 결과 전체 분석
python scripts/run_pending_analysis.py

# 목업 실행 결과 초기화
python scripts/reset_mock_runtime.py

# YOLO 목업 결과 한 줄 추가
python scripts/add_mock_yolo_result.py --drain-id 101 --obstruction-ratio 0.72 --confidence-score 0.91 --status 막힘

# 목업 원천 데이터 재생성
python scripts/generate_mock_data.py

# 합성 학습 데이터로 baseline 재학습
python scripts/train_mock_model.py

# 테스트
python -m pytest
```

## 4. 출력 개념

XGBoost 분석 결과는 단순히 `good/caution/danger`만 반환하지 않습니다.

```json
{
  "risk_score": 0.991,
  "risk_level": "danger",
  "analysis_status": "completed",
  "data_quality": "valid",
  "state_code": "INTERNAL_OR_DOWNSTREAM_OBSTRUCTION_SUSPECTED",
  "reason_codes": [
    "WATER_LEVEL_VERY_HIGH",
    "WATER_LEVEL_RISING_FAST",
    "FLOW_VELOCITY_LOW"
  ],
  "final_decision": "field_check"
}
```

역할 분리는 다음과 같습니다.

| 필드 | 의미 |
|---|---|
| `risk_score` | danger 클래스 확률 |
| `risk_level` | XGBoost 위험 단계: `good`, `caution`, `danger`, `unknown` |
| `state_code` | YOLO·센서 조합으로 해석한 상태 유형 |
| `analysis_status` | 분석 완료/저하/생략 여부 |
| `data_quality` | 센서·YOLO 입력 데이터 신뢰도 |
| `reason_codes` | 판단 근거 코드 목록 |
| `final_decision` | 운영 대응 코드 |

## 5. 현재 지원하는 주요 상태 코드

```text
NORMAL_DRAINAGE
SURFACE_OBSTRUCTION_LIKELY
DRY_SURFACE_OBSTRUCTION
COMBINED_OBSTRUCTION
SEVERE_OBSTRUCTION
INTERNAL_OR_DOWNSTREAM_OBSTRUCTION_SUSPECTED
PROGRESSIVE_OBSTRUCTION
INTERMITTENT_OBSTRUCTION
HYDRAULIC_OVERLOAD
HIGH_INFLOW_WITH_SURFACE_OBSTRUCTION
NEAR_CAPACITY_STABLE
RECOVERING
VISION_SENSOR_CONFLICT
SENSOR_DETECTED_HIDDEN_RISK
WATER_LEVEL_SPIKE
FLOW_SENSOR_STUCK
SENSOR_OSCILLATION
STALE_SENSOR_DATA
NO_VALID_SENSOR_DATA
LOW_CONFIDENCE_VISION
```

## 6. YOLO PoC 선택 실행

YOLO는 기본 XGBoost 환경에 포함하지 않습니다. 임시 PoC 추론이 필요한 경우에만 추가 설치합니다.

```bash
python -m pip install -r requirements/yolo-poc.txt
python yolo/cli.py --image path/to/image.jpg --drain-id 101
```

해당 CLI는 `yolo_result_data.jsonl`에 DB 테이블 형태의 결과를 추가합니다. XGBoost 코드는 YOLO 모듈을 직접 import하지 않습니다.

## 7. 주의사항

- 포함된 XGBoost 모델은 합성 목업 데이터로 학습한 개발용 baseline입니다.
- 실제 현장 성능 근거로 사용하면 안 됩니다.
- 실제 PostgreSQL 연동 시 `docs/DB_INTEGRATION_NOTES.md`의 미확정 항목을 팀과 먼저 확정해야 합니다.
- 전체 프로젝트 문서 요약과 원본은 `docs/`에 포함되어 있습니다.
- 새 개발 세션을 시작할 때는 `START_PROMPT.md`를 붙여 넣어 컨텍스트를 고정하세요.
