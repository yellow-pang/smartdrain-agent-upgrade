# 1단계 작업 프롬프트

너는 팀 프로젝트의 `ai_service/` 영역을 담당하는 Python 엔지니어다.

이번 작업은 **1단계: fake YOLO stub 추가 및 기본 테스트 작성**이다.

작업 전 저장소 루트의 `AGENTS.md`가 있으면 먼저 읽고 따른다. 또한 `ai_service/AGENTS.md`를 반드시 읽고 따른다.

작업 전 현재 파일 구조를 확인하고, 기존 구조와 충돌하지 않게 최소 변경으로 진행한다.

작업 완료 후 `ai_service/AGENTS.md`의 커밋 규칙에 맞춰 적절한 타입과 한글 설명으로 커밋한다.

## 작업 목표

실제 YOLO가 아직 없으므로, 백엔드-AI 서버 연결 흐름을 테스트할 수 있는 fake YOLO predictor를 만든다.

이 작업은 실제 YOLO 구현이 아니다.

## 작업 범위

수정 가능 범위:

ai_service/_yolo/**
ai_service/pytest.ini
ai_service/README.md
ai_service/AI_SERVICE_PLAN.md
ai_service/NEXT_STEP_PROMPT.md

하지 말 것:

- 실제 YOLO 구현
- YOLO 학습
- 이미지 처리 구현
- CCTV API 호출 구현
- DB 조회/저장 구현
- WebSocket 구현
- FastAPI/Flask endpoint 구현
- 백엔드 callback 실제 HTTP 전송 구현
- XGBoost 계약 변경
- 프론트엔드 수정

## 구현할 구조

없으면 아래 구조로 만든다.

ai_service/_yolo/
├─ __init__.py
├─ constants.py
├─ fake_yolo_predictor.py
├─ README.md
└─ tests/
   └─ test_fake_yolo_predictor.py

## YOLO 결과 계약

fake YOLO predictor는 아래 dict를 반환한다.

{
    "obstruction_ratio": 0.82,
    "confidence_score": 0.94,
    "yolo_status": "blocked",
}

필드는 반드시 아래 3개를 포함한다.

obstruction_ratio
confidence_score
yolo_status

허용 `yolo_status`:

good
dirty
blocked
unknown

## 구현 기준

- 입력은 `drain_id`이다.
- drain_id별 mock YOLO 결과를 deterministic하게 반환한다.
- MVP mock drain id는 1, 2, 3, 4를 우선 지원한다.
- 알 수 없는 drain_id는 `unknown` 결과로 처리한다.
- 실제 이미지 파일을 읽지 않는다.
- 실제 YOLO 모델을 로딩하지 않는다.
- CCTV API를 호출하지 않는다.

## 테스트

`ai_service/_yolo/tests/test_fake_yolo_predictor.py`를 작성한다.

테스트 항목:

1. 지원하는 drain_id는 dict 결과를 반환한다.
2. 결과 dict에 `obstruction_ratio`, `confidence_score`, `yolo_status`가 있다.
3. `yolo_status`는 허용 값 중 하나다.
4. 같은 drain_id는 항상 같은 결과를 반환한다.
5. 알 수 없는 drain_id는 `unknown` 결과를 반환한다.

`ai_service/pytest.ini`의 `testpaths`에 `_yolo/tests`를 추가한다.

## 검증

아래 명령이 통과해야 한다.

python -m pytest ai_service

venv 기준:

ai_service\.venv\Scripts\python.exe -m pytest ai_service

## 완료 후 갱신

작업 완료 후 `ai_service/NEXT_STEP_PROMPT.md`를 다음 단계인 `analysis orchestration 추가` 프롬프트로 갱신한다.

완료 후 아래를 보고한다.

- 생성/수정한 파일
- fake YOLO 결과 계약
- 테스트 결과
- 이후 2단계 analysis orchestration 작업 가능 여부

가능하면 변경 범위를 작게 유지하고, 기존 코드 스타일을 따르며, 불필요한 추상화는 만들지 않는다.
