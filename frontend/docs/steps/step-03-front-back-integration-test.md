# 03_front-back integration test 작업 기록

## 1. 작업 개요

| 항목 | 내용 |
|---|---|
| 브랜치 | `text/front-back-first-merge-test` |
| 병합 대상 | `feature/frontend` |
| 작업 범위 | `/frontend/docs` 문서 중심, 프론트-백엔드 통합 테스트 준비 및 기록 |
| 작업 목적 | SmartDrain MVP API 명세 기준으로 backend와 frontend가 실제로 데이터를 주고받는지 확인 |
| 테스트 기준 문서 | `frontend/docs/front-back-integration-test-guideline.md` |

이번 작업은 기존 plan 문서 대신 통합 테스트 전용 가이드 문서를 만들고, 해당 문서를 따라 Swagger 기준으로 backend API와 frontend 화면 연동을 확인하기 위한 작업이다.

```text
FastAPI Swagger 테스트
→ REST API 응답 확인
→ WebSocket 이벤트 확인
→ Next.js 화면 표시 확인
→ 발견 이슈 기록
```

## 2. 변경 내용

| 구분 | 변경 내용 |
|---|---|
| 통합 테스트 가이드 | `frontend/docs/front-back-integration-test-guideline.md` 추가 |
| 테스트 방식 정리 | PowerShell 혼용 대신 Swagger 기준 테스트 절차로 정리 |
| 실행 환경 정리 | Python 3.12, PostgreSQL, FastAPI, Next.js 실행 순서 기록 |
| API 생성 테스트 | `POST /api/drains`, `POST /api/sensor-data`, `POST /api/analysis/yolo`, `POST /api/analysis/xgboost` 순서 정리 |
| API 조회 테스트 | `GET /api/drains`, 상세, 센서 이력, 위험 이력, 최신 분석, 대시보드 요약 조회 기준 정리 |
| WebSocket 테스트 | `ws://localhost:8000/ws/drains/status` 연결 및 `DRAIN_STATUS_UPDATED` 확인 방법 정리 |
| 오류 대응 | Python 3.14 대신 Python 3.12 사용 권장, `CORS_ORIGINS` list 파싱 주의사항 기록 |
| 이슈 기록 양식 | 테스트 중 발견한 문제를 재현 순서, 기대 결과, 실제 결과, 심각도로 기록할 수 있게 표 추가 |

## 3. 테스트 기준

| 영역 | 기준 |
|---|---|
| Backend URL | `http://localhost:8000` |
| Swagger URL | `http://localhost:8000/docs` |
| Frontend URL | `http://localhost:3000` |
| Frontend env | `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` |
| Python | 3.12 기준 |
| REST 응답 | `ApiResponse<T>` 또는 `ApiListResponse<T>` wrapper |
| 필드명 | camelCase |
| 위험도 코드 | `good`, `caution`, `danger`, `unknown` |
| 막힘률 | `obstructionRatio` 0~1 ratio |

## 4. 테스트 흐름

| 단계 | 확인 내용 | 상태 |
|---|---|---|
| 1 | PostgreSQL 컨테이너 실행 | 사용자 수동 테스트 완료 |
| 2 | Python 3.12 venv 생성 및 의존성 설치 | 사용자 수동 테스트 완료 |
| 3 | `cd backend` 후 `python -m alembic upgrade head` 실행 | 사용자 수동 테스트 완료 |
| 4 | FastAPI 서버 실행 및 Swagger 접속 | 사용자 수동 테스트 완료 |
| 5 | Swagger에서 테스트 데이터 생성 API 실행 | 사용자 수동 테스트 완료 |
| 6 | Swagger에서 REST 조회 API 실행 | 사용자 수동 테스트 완료 |
| 7 | WebSocket 이벤트 수신 확인 | 사용자 수동 테스트 완료 또는 확인 필요 |
| 8 | Next.js 대시보드와 상세 페이지 확인 | 사용자 수동 테스트 완료 또는 확인 필요 |

세부 결과값과 실패 항목은 테스트 실행자가 `front-back-integration-test-guideline.md`의 체크리스트와 이슈 기록 양식에 이어서 기록한다.

## 5. 테스트 중 확인한 환경 이슈

| 이슈 | 원인 | 대응 |
|---|---|---|
| Python 3.14 사용 시 의존성 리스크 | `opencv-python`, `ultralytics`, `xgboost`, `psycopg[binary]`가 최신 Python에서 설치 또는 실행 문제가 날 수 있음 | Python 3.12 기준으로 venv 생성 |
| `python -m alembic upgrade head` 설정 파싱 오류 | `CORS_ORIGINS`가 list 설정인데 단일 문자열로 읽히면 pydantic-settings에서 JSON 파싱 오류 발생 가능 | `backend/.env`에서 `CORS_ORIGINS=["http://localhost:3000"]` 형식 확인 |
| Swagger/PowerShell 혼용 혼란 | 테스트 문서에 두 방식이 섞이면 진행자가 어떤 도구를 써야 하는지 헷갈릴 수 있음 | 첫 통합 테스트는 Swagger 기준으로 통일 |

## 6. 변경 전/후

| 항목 | 변경 전 | 변경 후 |
|---|---|---|
| 통합 테스트 절차 | API 명세서에는 테스트 순서가 있었지만 실제 진행자가 따라 하기에는 도구와 입력 위치가 분산됨 | Swagger 기준 실행 순서와 입력값을 단계별로 정리 |
| 테스트 데이터 생성 | POST API 순서의 의미가 명확하지 않음 | 빗물받이 생성 → 센서 저장 → YOLO 저장 → XGBoost 판단 흐름으로 설명 |
| 조회 테스트 | PowerShell 예시와 Swagger 기준이 섞임 | Swagger에서 GET API를 실행하는 방식으로 통일 |
| 이슈 기록 | 별도 양식 없음 | 발견 위치, 재현 순서, 기대/실제 결과, 심각도 기록 양식 추가 |

## 7. 남은 리스크

| 리스크 | 설명 |
|---|---|
| 상세 테스트 결과 미기록 | 현재 문서는 통합 테스트 완료를 위한 기준과 절차를 정리한 문서이며, 실제 응답 body 전문이나 스크린샷은 별도 기록이 필요하다. |
| WebSocket 화면 자동 반영 | 백엔드 이벤트 수신과 프론트 화면 자동 갱신은 구분해서 확인해야 한다. |
| 테스트 데이터 ID 혼동 | Swagger 응답의 숫자 `data.id`와 프론트 표시용 `DR-INT-001` 식별자를 혼동하지 않아야 한다. |
| 환경변수 포맷 | `.env`와 `.env.example`의 `CORS_ORIGINS` 포맷이 실제 `Settings` 타입과 맞는지 병합 전 확인이 필요하다. |

## 8. 추천 커밋 메시지

제목:

```text
docs: 프론트-백엔드 통합 테스트 문서 정리
```

내용:

```text
- Swagger 기준 프론트-백엔드 통합 테스트 가이드를 추가한다.
- 테스트 데이터 생성, REST 조회, WebSocket 확인 절차를 정리한다.
- Python 3.12와 CORS_ORIGINS 설정 등 테스트 환경 주의사항을 문서화한다.
```
