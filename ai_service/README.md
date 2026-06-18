# AI Service

이 폴더는 팀 프로젝트의 AI 서비스 영역입니다. 현재 관리 대상은 XGBoost 기반 빗물받이 침수 위험 판단 모듈입니다.

루트 `docs/`는 전체 기획 문서이며, 이 폴더의 `xgboost/docs/`는 XGBoost 구현과 연동 계약만 다룹니다.

## 현재 구조

```text
ai_service/
├─ pyproject.toml
├─ .venv/                    # 현재 로컬 가상환경
├─ README.md
└─ xgboost/
   ├─ src/                   # flood_risk_xgb 패키지
   ├─ tests/                 # XGBoost 테스트
   ├─ models/                # 목업 XGBoost 모델과 metadata
   ├─ scripts/               # 실행, 검증, 목업 데이터 관리 스크립트
   ├─ mock_data/             # JSONL fixture와 runtime 출력
   ├─ shared/contracts/      # DB-shaped JSON 계약
   ├─ docs/                  # XGBoost 전용 문서
   ├─ requirements.txt       # XGBoost 개발/검증/DB 연동 의존성
   └─ .env.example
```

`yolo/` 코드는 제거했습니다. XGBoost는 YOLO를 실행하지 않고, 이미 저장된 `yolo_result` 형태의 결과 레코드만 입력으로 사용합니다.

## 처리 흐름

```text
CCTV/OpenCV/YOLO 결과가 DB 또는 목업 JSONL에 저장됨
→ XGBoost가 yolo_result_id 기준으로 YOLO 결과 조회
→ 같은 drain_id의 센서 이력 조회
→ 최근 YOLO 이력과 센서 이력으로 Feature 생성
→ XGBoost 모델 예측
→ data_quality, state_code, reason_codes, final_decision 산출
→ xgboost_data 형태로 결과 저장
```

## 실행

현재 만들어진 가상환경을 사용할 때는 `ai_service` 루트에서 실행합니다.

```powershell
cd C:\dev_work\team_proj_01\smartdrain\ai_service
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\.venv\Scripts\Activate.ps1
python xgboost\scripts\verify_setup.py
python -m pytest
deactivate
```

새 환경을 다시 만들 때는 단일 의존성 파일을 사용합니다.

```powershell
python -m pip install -r xgboost\requirements.txt
python -m pip install -e .
```

## 자주 쓰는 명령

```powershell
# 18개 목업 시나리오 검증
python xgboost\scripts\verify_setup.py

# 전체 테스트
python -m pytest

# runtime 결과 초기화
python xgboost\scripts\reset_mock_runtime.py

# 아직 처리되지 않은 목업 YOLO 결과 전체 분석
python xgboost\scripts\run_pending_analysis.py

# 특정 YOLO 결과 1건 분석
python xgboost\scripts\run_analysis.py --yolo-result-id 1

# 사용자가 직접 YOLO 목업 결과 1건 추가
python xgboost\scripts\add_mock_yolo_result.py --drain-id 101 --obstruction-ratio 0.72 --confidence-score 0.91 --status 막힘
```

결과 파일은 아래 위치에 생성됩니다.

```text
xgboost/mock_data/runtime/xgboost_data.jsonl
xgboost/mock_data/runtime/analysis_trace.jsonl
```

## 핵심 제약

- XGBoost는 YOLO 코드나 YOLO 모델 파일을 직접 import/load하지 않습니다.
- `yolo_result`는 외부 비전 분석 결과를 표현하는 입력 계약입니다.
- 센서 Feature는 `sensor.measured_at <= yolo_result.captured_at` 데이터만 사용합니다.
- `unknown`은 학습 클래스가 아니라 데이터 품질 문제로 인한 분석 보류 결과입니다.
- Feature 순서는 `xgboost/models/model_metadata.json`과 일치해야 합니다.
- 현재 모델은 synthetic mock baseline이며 실제 현장 성능 근거가 아닙니다.

## 주요 문서

| 문서 | 용도 |
|---|---|
| `xgboost/README.md` | XGBoost 모듈 상세 설명 |
| `xgboost/docs/XGBOOST_SCOPE.md` | 담당 범위와 제외 범위 |
| `xgboost/docs/SCENARIO_MATRIX.md` | 18개 목업 시나리오 설명 |
| `xgboost/docs/DATA_CONTRACT.md` | YOLO 결과, 센서, XGBoost 결과 계약 |
| `xgboost/docs/DB_INTEGRATION_NOTES.md` | PostgreSQL 연동 전 확인 사항 |
| `xgboost/docs/DECISIONS_PENDING.md` | 팀 결정이 필요한 항목 |
