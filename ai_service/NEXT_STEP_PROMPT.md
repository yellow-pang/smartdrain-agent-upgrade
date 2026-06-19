# 다음 단계 작업 프롬프트

너는 팀 프로젝트의 `ai_service/` 영역을 담당하는 Python 엔지니어다.

이번 작업은 **HTTP endpoint 스켈레톤 구현 또는 callback sender 런타임 추가**이다.

작업 전 저장소 루트의 `AGENTS.md`가 있으면 먼저 읽고 따른다. 또한 `ai_service/AGENTS.md`를 반드시 읽고 따른다.

작업 전 현재 파일 구조를 확인하고, 기존 구조와 충돌하지 않게 최소 변경으로 진행한다.

작업 완료 후 `ai_service/AGENTS.md`의 커밋 규칙에 맞춰 적절한 타입과 한글 설명으로 커밋한다.

## 선택 기준

서버 프레임워크가 확정되었다면 `/ai/analysis/run` HTTP endpoint 스켈레톤을 구현한다.

서버 프레임워크가 아직 미확정이라면 endpoint 코드와 callback sender 런타임을 만들지 않고, 문서만 보강한다.

## 현재 기준 계약

현재 `ai_service`는 비동기 AI 분석 API 문서를 기준으로 한다.

사용 endpoint:

POST /ai/analysis/run
POST /api/ai-callback/yolo-result
POST /api/ai-callback/xgboost-result

현재 내부 entrypoint:

from ai_service.analysis.service import run_analysis_job

현재 job_id 정책:

job_id = AI_JOB_{request_id}

YOLO status 허용 값:

good
dirty
blocked
unknown

## 책임 경계

백엔드 HTTP 통신은 future `ai_service/http` 계층에서만 수행한다.

`analysis`는 orchestration과 callback-ready payload dict 생성까지만 담당한다.

`_yolo`는 `drain_id`를 받아 YOLO 결과 dict를 반환하는 predictor-only 모듈이다.

`xgboost`는 feature batch를 받아 risk 결과 dict를 반환하는 predictor-only 모듈이다.

`_yolo`, `xgboost`, `analysis` 안에서 백엔드 API 호출, callback 전송, FastAPI import, backend URL 관리, timeout/retry 처리를 하지 않는다.

## callback sender MVP 정책

HTTP 계층이 추가되면 callback sender는 best-effort로 동작한다.

- accepted 응답은 callback 성공/실패와 분리한다.
- YOLO callback 실패 후에도 XGBoost callback은 시도한다.
- callback 요청마다 timeout을 둔다.
- callback 요청마다 최대 1회만 재시도한다.
- 재시도 실패 후에는 로그만 남기고 persistent retry queue는 만들지 않는다.

## 작업 범위

수정 가능 범위:

ai_service/**

하지 말 것:

- 실제 YOLO 구현
- fake YOLO mock 값 변경
- 이미지 처리 구현
- CCTV API 호출 구현
- 실제 XGBoost 학습 또는 모델 로딩
- DB 조회/저장 구현
- WebSocket 구현
- 백엔드 callback 실제 HTTP 전송 구현
- 프론트엔드 수정
- XGBoost public contract 변경

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
- 선택한 작업 방향
- 테스트 결과
- 커밋 해시와 커밋 메시지
- 이후 단계 작업 가능 여부

가능하면 변경 범위를 작게 유지하고, 기존 코드 스타일을 따르며, 불필요한 추상화는 만들지 않는다.
