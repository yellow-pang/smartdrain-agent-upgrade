# 3단계 작업 프롬프트

너는 팀 프로젝트의 `ai_service/` 영역을 담당하는 Python 엔지니어다.

이번 작업은 **3단계: analysis 계약 세분화 및 예시 실행 문서화**이다.

작업 전 저장소 루트의 `AGENTS.md`가 있으면 먼저 읽고 따른다. 또한 `ai_service/AGENTS.md`를 반드시 읽고 따른다.

작업 전 현재 파일 구조를 확인하고, 기존 구조와 충돌하지 않게 최소 변경으로 진행한다.

작업 완료 후 `ai_service/AGENTS.md`의 커밋 규칙에 맞춰 적절한 타입과 한글 설명으로 커밋한다.

예상 커밋 메시지:

docs: AI 분석 흐름 계약 문서 보강

## 작업 목표

이미 구현된 `ai_service/analysis` 내부 orchestration을 백엔드 연동 전에 더 명확히 문서화한다.

이번 단계는 실제 HTTP endpoint 구현이 아니라, 백엔드와 맞출 입력/출력 예시와 error policy를 정리하는 문서 중심 작업이다.

## 작업 범위

수정 가능 범위:

ai_service/analysis/**
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

## 해야 할 일

1. `ai_service/analysis/README.md`에 실제 예시 payload와 반환 예시를 더 명확히 작성한다.
2. accepted response, YOLO callback payload, XGBoost callback payload 예시를 문서화한다.
3. `quality_status != valid`와 필수 key 누락 시 `ValueError`가 발생한다는 정책을 문서화한다.
4. sensor normalization 기준을 백엔드가 이해할 수 있게 설명한다.
5. 필요하면 `ai_service/analysis/examples/`에 작은 예시 JSON 파일을 추가한다. 단, 외부 API 호출이나 DB 접근은 하지 않는다.
6. 테스트가 계속 통과하는지 확인한다.

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
- 문서화한 analysis 계약
- 테스트 결과
- 커밋 해시와 커밋 메시지
- 이후 단계 작업 가능 여부

가능하면 변경 범위를 작게 유지하고, 기존 코드 스타일을 따르며, 불필요한 추상화는 만들지 않는다.
