# SmartDrain Verification Guide

## 1. 문서 목적

이 문서는 SmartDrain에서 코드, 설정, 문서 변경 후 어떤 검증을 선택하고 어떻게 결과를 보고할지 정의합니다.

실제 검증 명령은 각 서비스의 설정과 CI 구성을 우선합니다.

## 2. 기본 원칙

- 저장소에 실제 구성된 검증 도구만 사용합니다.
- 테스트 도구를 임의로 추가하지 않습니다.
- 새 검증 도구가 필요하면 사용자 승인을 받습니다.
- 변경 영향 범위에 맞는 검증을 선택합니다.
- 검증 실패를 숨기지 않습니다.
- 타입 검사와 빌드를 우회하지 않습니다.
- 기존 오류와 신규 오류를 가능한 범위에서 구분합니다.
- 외부 시스템 없이 실행 가능한 검증을 우선합니다.
- 실행하지 못한 검증은 이유를 기록합니다.

## 3. 검증 전 확인

검증 명령을 실행하기 전에 다음을 확인합니다.

- `package.json`
- `requirements.txt`
- 테스트 설정
- CI 설정
- Dockerfile
- Docker Compose
- README 실행 명령
- 환경변수 요구사항
- 모델 파일 요구사항
- 외부 DB 또는 네트워크 요구사항

문서의 예시 명령보다 실제 설정을 우선합니다.

## 4. 변경 범위별 검증

| 변경 종류            | 최소 검증                            |
| -------------------- | ------------------------------------ |
| 문서만 변경          | 링크, 경로, 내용 일치 확인           |
| Frontend 컴포넌트    | lint, TypeScript                     |
| Frontend 데이터 흐름 | lint, TypeScript, build, 관련 테스트 |
| Backend API          | import 검사, 관련 pytest             |
| DB 모델              | pytest, migration 검토               |
| AI 분석 로직         | 관련 단위 테스트, import 검사        |
| API 계약             | producer와 consumer 양쪽 검증        |
| WebSocket            | 연결, payload, 재연결, consumer 검증 |
| Docker               | image build 또는 Compose config      |
| Nginx                | 설정 문법과 proxy 경로               |
| CI/CD                | pipeline 문법, 참조 경로, parameter  |

## 5. Frontend 검증

작업 전 `frontend/package.json`의 scripts를 확인합니다.

현재 `frontend/package.json`의 script는 `dev`, `build`, `start`, `lint`입니다. TypeScript 검사는 script가 아니라 직접 명령으로 실행합니다.

기본 검증 후보:

```bash
cd frontend
pnpm lint
pnpm exec tsc --noEmit
pnpm build
```

실제 테스트 script가 있으면 관련 테스트를 실행합니다.

확인할 내용:

- TypeScript 오류
- ESLint 오류
- production build
- import 경로
- client와 server component 경계
- 환경변수 참조
- API DTO와 UI 타입
- 로딩과 오류 상태
- 이미지 전환 상태
- 반응형 overflow

## 6. Backend 검증

작업 전 다음을 확인합니다.

- Python 버전
- `requirements.txt`
- pytest 설정
- 실행 진입점
- DB 연결 요구사항
- Alembic 설정

현재 Backend 의존성 파일은 `backend/requirements.txt`이고 Docker 실행 진입점은 `app.main:app`입니다. 현재 저장소에는 Backend pytest 설정과 테스트 파일이 확인되지 않으므로, Backend 테스트 명령은 실제 테스트가 추가된 경우 실행합니다.

테스트가 구성된 경우의 검증 후보:

```bash
cd backend
python -m pytest
```

필요한 경우:

```bash
python -m compileall .
```

확인할 내용:

- import 오류
- Pydantic schema
- API status code
- 오류 응답
- DB transaction
- migration 필요 여부
- WebSocket payload
- callback consumer
- 환경변수 누락 처리

## 7. AI Service 검증

작업 전 다음을 확인합니다.

- Python 버전
- `requirements.txt`
- 모델 파일 위치
- pytest 설정
- callback 환경변수
- Docker 실행 방식

현재 AI Service 의존성 파일은 `ai_service/requirements.txt`, pytest 설정은 `ai_service/pytest.ini`, Docker 실행 진입점은 `ai_service.http.app:app`입니다.

기본 검증 후보:

```bash
cd ai_service
python -m pytest
```

필요한 경우:

```bash
python -m compileall .
```

확인할 내용:

- 모델 없이 실행 가능한 테스트
- 입력 validation
- OpenCV 전처리
- YOLO 결과 adapter
- XGBoost 입력과 출력
- 위험 상태 mapping
- callback payload
- timeout과 retry
- HTTP 오류 mapping

## 8. API 계약 변경 검증

API 계약을 변경하면 다음을 함께 확인합니다.

### Producer

- endpoint
- request schema
- response schema
- status code
- 오류 응답

### Consumer

- API client
- DTO
- adapter
- UI 처리
- 테스트
- 문서

한쪽 서비스 테스트만으로 계약 변경 검증을 끝내지 않습니다.

## 9. WebSocket 검증

WebSocket 변경 시 다음을 확인합니다.

- 연결 URL
- 인증 여부
- upgrade proxy
- event type
- payload 필드
- 날짜 형식
- 위험 상태 enum
- 연결 종료
- 재연결
- backoff
- 중복 메시지
- 최신값 보정
- REST 데이터와의 정합성

Nginx를 사용하는 경우 WebSocket upgrade header도 확인합니다.

## 10. AI Callback 검증

callback 변경 시 다음을 확인합니다.

- callback URL
- request 식별자
- drain 식별자
- 결과 payload
- 오류 payload
- Backend response
- timeout
- retry
- 중복 callback
- 순서가 뒤바뀐 결과
- DB 중복 저장
- 실패 로그

AI Service와 Backend 양쪽 테스트를 확인합니다.

## 11. DB 및 Alembic 검증

DB 변경 시 다음을 확인합니다.

- 모델과 migration 일치
- upgrade SQL
- downgrade 가능 여부
- nullable
- default
- server default
- index
- unique constraint
- foreign key
- 기존 데이터 영향
- 배포 순서

운영 데이터가 있는 환경에서 파괴적 변경이 발생할 수 있으면 사용자에게 명확히 보고합니다.

## 12. Docker 검증

Docker 관련 변경 시 다음을 확인합니다.

- Dockerfile 경로
- build context
- COPY 경로
- workdir
- 사용자 권한
- environment
- healthcheck
- port
- volume
- startup command

가능한 경우 다음 명령을 사용할 수 있습니다.

```bash
docker compose config
docker compose -f docker-compose.yml -f docker-compose.dev.yml config
```

실제 build는 범위와 환경 자원을 고려하여 실행합니다.

volume 삭제가 포함된 명령은 사용자 승인 없이 실행하지 않습니다.

## 13. Nginx 검증

Nginx 변경 시 다음을 확인합니다.

- upstream
- proxy_pass
- API 경로
- WebSocket upgrade
- static 경로
- timeout
- client body size
- same-origin 구성
- healthcheck 경로

가능한 경우 설정 문법 검사를 수행합니다.

컨테이너 내부 검사 명령은 실제 서비스 이름을 확인한 뒤 사용합니다.

## 14. CI/CD 검증

CI/CD 변경 시 다음을 확인합니다.

- pipeline 문법
- branch 조건
- parameter
- environment
- secret 참조
- working directory
- Docker 경로
- build artifact
- 배포 순서
- rollback 가능성
- 실패 처리

현재 CI/CD 관련 파일은 루트 `Jenkinsfile`, `.jenkins/scripts/`, `jenkins/`입니다. GitHub Actions 설정은 현재 저장소에서 확인되지 않습니다.

실제 배포 실행은 사용자가 명시적으로 요청한 범위 안에서만 진행합니다.

## 15. 파일 이동 후 검증

파일 또는 디렉터리 이동 후 다음을 확인합니다.

- TypeScript import
- Python import
- Docker COPY
- volume
- CI 경로
- 테스트 경로
- 문서 링크
- 환경변수 파일 경로
- 실행 진입점

검색으로 이전 경로가 남아 있는지도 확인합니다.

## 16. 검증 결과 기록

검증 결과는 다음 형식으로 작성할 수 있습니다.

| 검증 항목           | 결과             | 비고                |
| ------------------- | ---------------- | ------------------- |
| 명령 또는 확인 항목 | 성공/실패/미실행 | 상세 결과 또는 이유 |

상태 기준:

- 성공: 검증을 실행했고 정상 완료
- 실패: 검증을 실행했지만 오류 발생
- 미실행: 환경이나 범위 문제로 실행하지 못함
- 해당 없음: 변경 범위와 무관함

## 17. 실패 보고

검증 실패 시 다음을 작성합니다.

1. 실패한 명령
2. 핵심 오류
3. 이번 변경과의 관련 여부
4. 기존 오류인지 여부
5. 해결 또는 추가 확인에 필요한 사항
6. 현재 작업 결과에 미치는 영향

실패를 성공으로 표현하거나 중요한 오류를 생략하지 않습니다.
