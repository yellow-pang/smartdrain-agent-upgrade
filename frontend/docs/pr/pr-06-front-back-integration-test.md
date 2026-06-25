## PR 제목

[docs] # 프론트-백엔드 통합 테스트 문서 정리

## 작업 내용

- SmartDrain MVP 프론트엔드-백엔드 첫 통합 테스트를 위한 가이드 문서를 추가했습니다.
    - `frontend/docs/front-back-integration-test-guideline.md`에 테스트 전 확인, 실행 준비, 테스트 데이터 생성, REST 조회, WebSocket 확인, 프론트 화면 확인 기준을 정리했습니다.
    - 테스트 진행 도구는 Swagger 기준으로 통일했습니다.
    - PowerShell 예시는 첫 통합 테스트 흐름에서 제외해 진행자가 Swagger 화면만 따라가도 테스트할 수 있게 정리했습니다.
- 통합 테스트 환경 기준을 문서화했습니다.
    - Python 3.12 기준 venv 생성
    - PostgreSQL 컨테이너 실행
    - FastAPI 서버와 Swagger 접속
    - Next.js 개발 서버와 `NEXT_PUBLIC_API_BASE_URL` 설정
- API 명세 기준 체크리스트를 정리했습니다.
    - REST 응답 wrapper 확인
    - camelCase 필드 확인
    - 위험도 코드 확인
    - 수위, 유속, 막힘률 단위 확인
    - `DRAIN_STATUS_UPDATED` WebSocket 이벤트 확인
- 테스트 중 헷갈릴 수 있는 지점을 보완했습니다.
    - 테스트 데이터 생성 순서의 의미를 설명했습니다.
    - `drainId`, `sensorDataId`, `yoloResultId`는 Swagger 응답의 숫자 ID를 사용해야 한다는 점을 명시했습니다.
    - Python 3.14 사용 시 의존성 문제가 날 수 있어 Python 3.12 기준으로 진행하도록 정리했습니다.
    - `CORS_ORIGINS` 설정이 pydantic-settings에서 list로 읽히는 점을 주의사항으로 기록했습니다.
- 병합 전 작업 기록 문서를 추가했습니다.
    - `frontend/docs/steps/step-03-front-back-integration-test.md`
    - `frontend/docs/pr/pr-06-front-back-integration-test.md`

## 주요 변경 파일

- `frontend/docs/front-back-integration-test-guideline.md`
    - Swagger 기준 통합 테스트 실행 가이드
    - 테스트 데이터 생성 순서
    - REST API 조회 체크리스트
    - WebSocket 테스트 방법
    - 프론트 화면 확인 기준
    - 에러 응답 테스트와 이슈 기록 양식
- `frontend/docs/steps/step-03-front-back-integration-test.md`
    - 통합 테스트 준비와 문서화 작업 기록
    - 테스트 기준, 환경 이슈, 남은 리스크 정리
- `frontend/docs/pr/pr-06-front-back-integration-test.md`
    - `feature/frontend` 병합 전 리뷰용 PR 요약 문서

## 스크린샷 / 테스트 결과

| 항목 | 결과 | 비고 |
|---|---|---|
| PostgreSQL 실행 | 사용자 수동 테스트 완료 | 세부 로그는 별도 확인 |
| `cd backend` 후 `python -m alembic upgrade head` | 사용자 수동 테스트 완료 | CORS 설정 파싱 이슈 확인 후 진행 |
| FastAPI Swagger | 사용자 수동 테스트 완료 | `http://localhost:8000/docs` 기준 |
| 테스트 데이터 생성 API | 사용자 수동 테스트 완료 | Swagger 기준 |
| REST 조회 API | 사용자 수동 테스트 완료 | Swagger 기준 |
| Next.js 화면 확인 | 사용자 수동 테스트 완료 또는 확인 필요 | 세부 화면 결과는 체크리스트에 기록 필요 |
| WebSocket 확인 | 사용자 수동 테스트 완료 또는 확인 필요 | 이벤트 수신과 화면 자동 반영을 구분해 기록 필요 |

## 비고

- 이번 PR은 기능 코드 변경보다 통합 테스트 진행과 병합 전 문서화에 초점을 둡니다.
- 실제 API 응답 body 전문, Swagger 스크린샷, 프론트 화면 스크린샷이 있다면 PR 본문에 추가하면 리뷰가 더 쉬워집니다.
- `feature/frontend` 병합 전 `.env.example`의 `CORS_ORIGINS` 값이 backend `Settings` 타입과 맞는지 확인이 필요합니다.
- WebSocket은 백엔드 이벤트 수신과 프론트 화면 자동 갱신을 별도 항목으로 기록하는 것이 좋습니다.
