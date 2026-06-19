# 4단계 작업 프롬프트

너는 팀 프로젝트의 `ai_service/` 영역을 담당하는 Python 엔지니어다.

이번 작업은 **4단계: HTTP API 연결 준비 범위 결정 및 스켈레톤 설계**이다.

작업 전 저장소 루트의 `AGENTS.md`가 있으면 먼저 읽고 따른다. 또한 `ai_service/AGENTS.md`를 반드시 읽고 따른다.

작업 전 현재 파일 구조를 확인하고, 기존 구조와 충돌하지 않게 최소 변경으로 진행한다.

작업 완료 후 `ai_service/AGENTS.md`의 커밋 규칙에 맞춰 적절한 타입과 한글 설명으로 커밋한다.

예상 커밋 메시지:

docs: AI 서버 HTTP 연결 설계 정리

## 작업 목표

현재 구현된 `ai_service/analysis.run_analysis_job`를 실제 백엔드 호출 구조에 연결하기 전에, HTTP API 계층을 어떤 방식으로 둘지 문서와 최소 설계로 정리한다.

이번 단계는 실제 서버 실행 구현이 아니라 연결 설계 단계다.

## 작업 범위

수정 가능 범위:

ai_service/**

하지 말 것:

- 실제 YOLO 구현
- 이미지 처리 구현
- CCTV API 호출 구현
- 실제 XGBoost 학습 또는 모델 로딩
- DB 조회/저장 구현
- WebSocket 구현
- 백엔드 callback 실제 HTTP 전송 구현
- 프론트엔드 수정
- XGBoost public contract 변경

## 해야 할 일

1. 현재 팀에서 사용할 서버 프레임워크가 정해졌는지 확인한다.
2. 프레임워크가 아직 정해지지 않았다면 실제 FastAPI/Flask 코드는 만들지 않는다.
3. `ai_service/README.md` 또는 별도 문서에 HTTP 연결 후보 구조를 정리한다.
4. `/ai/analysis/run`이 내부적으로 `run_analysis_job(payload)`를 호출하게 될 예정임을 문서화한다.
5. 실제 callback sender는 아직 구현하지 않고, 현재는 callback payload dict 생성까지만 담당한다고 명시한다.
6. 필요하면 `ai_service/analysis`의 public entrypoint 이름과 import 예시를 정리한다.
7. 테스트가 계속 통과하는지 확인한다.

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
- 정리한 HTTP 연결 설계
- 테스트 결과
- 커밋 해시와 커밋 메시지
- 이후 단계 작업 가능 여부

가능하면 변경 범위를 작게 유지하고, 기존 코드 스타일을 따르며, 불필요한 추상화는 만들지 않는다.
