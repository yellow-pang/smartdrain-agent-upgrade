# SmartDrain Backend Guidelines

이 파일은 `backend/` 내부 작업에 적용됩니다.

루트 `AGENTS.md`의 공통 규칙을 함께 적용합니다.

## 1. Backend 책임

Backend는 다음 책임을 가집니다.

- FastAPI REST API
- PostgreSQL 접근
- SQLAlchemy 모델
- Pydantic schema
- Alembic migration
- WebSocket 연결과 broadcast
- AI 분석 요청
- AI Service callback 수신
- 분석 결과 저장
- Frontend에 필요한 데이터 제공

Backend는 데이터 저장과 서비스 간 데이터 계약의 중심 역할을 담당합니다.

## 2. 디렉터리 기준

Backend 단독 실행에 필요한 파일은 `backend/` 아래에 둡니다.

기본 위치는 다음과 같습니다.

```text
backend/alembic.ini
backend/alembic/
backend/requirements.txt
```

실제 구조가 다르면 현재 저장소 구조를 우선하고 차이를 보고합니다.

## 3. API 작성 원칙

- 기존 router, service, repository 패턴을 먼저 확인합니다.
- router에 DB 처리와 비즈니스 로직을 직접 집중시키지 않습니다.
- request와 response schema를 명시적으로 구분합니다.
- HTTP status code와 오류 응답 형식을 일관되게 유지합니다.
- nullable 필드와 기본값의 의미를 명확히 합니다.
- 기존 API 경로와 응답 계약을 불필요하게 변경하지 않습니다.
- 하위 호환성을 깨는 변경은 사용자 승인 후 진행합니다.

## 4. REST, WebSocket 및 callback 계약

계약 변경 시 다음 항목을 함께 확인합니다.

- Backend request schema
- Backend response schema
- Frontend DTO
- Frontend adapter
- WebSocket payload 타입
- AI Service callback payload
- 관련 문서
- 관련 테스트

producer와 consumer를 한쪽만 변경하지 않습니다.

WebSocket 메시지는 이벤트 타입과 payload를 구분하고, 기존 이벤트 명칭과 필드명을 우선 유지합니다.

AI callback은 중복 요청, timeout, 재시도, 실패 응답 가능성을 고려합니다.

## 5. DB와 SQLAlchemy

- DB 접근 책임은 Backend에 둡니다.
- Frontend와 AI Service가 DB에 직접 접근하도록 만들지 않습니다.
- 모델 변경 전 기존 schema와 migration 상태를 확인합니다.
- PK, FK, unique constraint, index의 목적을 확인합니다.
- created_at과 updated_at의 생성 및 갱신 기준을 일관되게 유지합니다.
- 기록성 데이터는 추적 가능성과 중복 처리 방식을 고려합니다.
- transaction 범위와 실패 시 rollback을 확인합니다.

## 6. Alembic

DB schema 변경은 사용자 승인 후 진행합니다.

변경 시 다음을 확인합니다.

1. migration 필요 여부
2. upgrade 동작
3. downgrade 가능 여부
4. 기존 데이터 영향
5. nullable과 server default
6. index와 constraint 영향
7. 배포 순서
8. 기존 API와의 호환성

migration 파일을 수동으로 수정할 경우 생성된 SQL과 실제 모델 차이를 확인합니다.

## 7. 의존성

Backend 런타임 의존성은 `backend/requirements.txt`를 기준으로 관리합니다.

새 의존성 추가 전 다음을 확인합니다.

- 기존 패키지로 해결 가능한지
- 표준 라이브러리로 해결 가능한지
- 버전 호환성
- 런타임 영향
- 보안 및 유지보수 상태

패키지 추가, 교체, 삭제는 사용자 승인 후 진행합니다.

## 8. 환경변수

- DB 접속 정보는 환경변수로 관리합니다.
- 실제 값은 `.env`에 두고 Git에 커밋하지 않습니다.
- 새로운 환경변수는 `.env.example`에 이름과 설명만 추가합니다.
- 필수 환경변수가 없을 때 오류가 명확하게 나타나도록 합니다.
- 개발, 테스트, 운영 환경의 기본값을 혼동하지 않습니다.

## 9. 검증

검증 기준은 `docs/reference/verification-guide.md`를 우선 확인합니다.

작업 전 다음을 확인합니다.

- `requirements.txt`
- pytest 설정
- FastAPI 실행 진입점
- Alembic 설정
- Docker 실행 명령
- CI에서 사용하는 검증 명령

현재 Backend 의존성은 `backend/requirements.txt`로 관리하며 실행 진입점은 `app.main:app`입니다.

Backend pytest 설정이나 테스트 파일이 실제로 구성된 경우 다음을 실행합니다.

```bash
cd backend
python -m pytest
```

필요한 경우 다음도 확인합니다.

```bash
python -m compileall .
```

DB 없이 실행 가능한 단위 테스트를 우선합니다.

API 또는 계약 변경 시 Frontend와 AI Service 영향도 함께 점검합니다.

검증 실패를 숨기거나 테스트를 우회하지 않습니다.
