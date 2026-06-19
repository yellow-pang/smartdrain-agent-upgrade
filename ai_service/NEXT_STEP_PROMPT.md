# 2단계 작업 프롬프트

너는 팀 프로젝트의 `ai_service/` 영역을 담당하는 Python 엔지니어다.

이번 작업은 **2단계: analysis orchestration 추가**이다.

작업 전 저장소 루트의 `AGENTS.md`가 있으면 먼저 읽고 따른다. 또한 `ai_service/AGENTS.md`를 반드시 읽고 따른다.

작업 전 현재 파일 구조를 확인하고, 기존 구조와 충돌하지 않게 최소 변경으로 진행한다.

작업 완료 후 `ai_service/AGENTS.md`의 커밋 규칙에 맞춰 적절한 타입과 한글 설명으로 커밋한다.

이번 작업의 커밋 타입은 백엔드-AI 분석 흐름 기본 기능 추가이므로 `feat`를 우선 사용한다.

예상 커밋 메시지:

feat: AI 분석 흐름 기본 오케스트레이션 추가

## 작업 목표

실제 HTTP endpoint나 callback 전송 없이, 백엔드 분석 요청 payload를 받아 내부 분석 흐름을 한 번에 실행하는 orchestration 계층을 만든다.

흐름은 아래 순서다.

1. 백엔드 요청 payload 검증
2. job_id 생성
3. accepted response 생성
4. fake YOLO 실행
5. YOLO callback payload 생성
6. YOLO 결과와 센서값을 XGBoost 입력으로 변환
7. XGBoost 실행
8. XGBoost callback payload 생성

## 작업 범위

수정 가능 범위:

ai_service/analysis/**
ai_service/pytest.ini
ai_service/README.md
ai_service/AI_SERVICE_PLAN.md
ai_service/NEXT_STEP_PROMPT.md

하지 말 것:

- 실제 YOLO 구현
- 이미지 처리 구현
- CCTV API 호출 구현
- 실제 XGBoost 학습 또는 모델 로딩
- DB 조회/저장 구현
- WebSocket 구현
- FastAPI/Flask endpoint 구현
- 백엔드 callback 실제 HTTP 전송 구현
- 프론트엔드 수정
- XGBoost public contract 변경

## 입력 payload

analysis orchestration 함수는 아래 형태를 입력으로 받는다.

{
    "request_id": "REQ_20260618_001",
    "drain_id": 2,
    "sensor_data": {
        "measured_at": "2026-06-18T08:36:13+09:00",
        "water_level_cm": 98.13,
        "flow_velocity_mps": 0.4512,
        "quality_status": "valid",
    },
}

## 반환 형태

내부 함수는 실제 callback 전송 없이 아래 dict를 반환한다.

{
    "accepted_response": {...},
    "yolo_callback_payload": {...},
    "xgboost_callback_payload": {...},
}

## 구현 기준

- `ai_service/analysis/` 패키지를 만든다.
- fake YOLO는 `ai_service._yolo`의 predictor를 사용한다.
- XGBoost는 기존 `ai_service.xgboost.service.predict_flood_risk_batch`를 사용한다.
- 실제 HTTP endpoint는 만들지 않는다.
- 실제 callback 전송은 하지 않는다.
- DB 저장은 하지 않는다.
- job_id는 deterministic하거나 간단한 생성 규칙을 사용해도 된다.
- evaluated_at은 timezone-aware ISO 문자열로 생성한다.
- XGBoost callback의 `final_decision`은 backend 문서 기준 코드로 매핑한다.

권장 decision mapping:

good -> normal
caution -> monitoring
danger -> dispatch_required
unknown -> field_check

## 테스트

`ai_service/analysis/tests/` 아래에 테스트를 작성한다.

테스트 항목:

1. 정상 payload 입력 시 accepted response가 생성된다.
2. request_id와 job_id가 callback payload에 유지된다.
3. fake YOLO callback payload가 문서 구조를 따른다.
4. XGBoost callback payload가 문서 구조를 따른다.
5. XGBoost callback final_decision이 backend decision code로 매핑된다.
6. 필수 payload key가 빠지면 ValueError를 발생시킨다.
7. quality_status가 valid가 아니면 ValueError를 발생시킨다.

`ai_service/pytest.ini`의 `testpaths`에 `analysis/tests`를 추가한다.

## 검증

아래 명령이 통과해야 한다.

python -m pytest ai_service

venv 기준:

ai_service\.venv\Scripts\python.exe -m pytest ai_service

## 완료 후 갱신

작업 완료 후 `ai_service/NEXT_STEP_PROMPT.md`를 다음 단계 프롬프트로 갱신한다.

다음 단계 프롬프트도 삼중 백틱 없이 작성한다.

완료 후 아래를 보고한다.

- 생성/수정한 파일
- analysis orchestration 입력/출력 계약
- 테스트 결과
- 커밋 해시와 커밋 메시지
- 이후 단계 작업 가능 여부

가능하면 변경 범위를 작게 유지하고, 기존 코드 스타일을 따르며, 불필요한 추상화는 만들지 않는다.
