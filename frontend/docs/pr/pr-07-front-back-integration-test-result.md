## PR 제목

[docs] # 프론트-백엔드 API 연동 통합 테스트 결과 문서 보강

## 작업 내용

- SmartDrain MVP 프론트엔드-백엔드 REST API 연동 테스트 결과 문서를 추가했습니다.
    - `docs/12_프론트엔드_백엔드_API연동_테스트_문서.md`에 테스트 목적, 범위, 환경, 진행 순서, 테스트 결과, 발견 이슈, 남은 리스크를 정리했습니다.
    - `frontend/docs/API연동back-front통합테스트정리.md`에도 동일한 테스트 완료 문서를 추가해 프론트엔드 문서 폴더 안에서도 결과를 확인할 수 있게 했습니다.
- 통합 테스트 가이드라인을 실제 진행 흐름에 맞게 보강했습니다.
    - Python 3.12 기준 실행 방법을 유지하면서 Anaconda/Miniconda 환경 생성 예시를 추가했습니다.
    - Swagger 기준 테스트 데이터 생성 순서와 REST API 조회 체크리스트의 표 형식을 정리했습니다.
    - 테스트 후 정리, 완료 기준, 이슈 기록 양식을 보기 쉽게 다듬었습니다.
- 프론트엔드 API base URL 예시 파일을 추가했습니다.
    - `frontend/.env.example`에 `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` 값을 명시했습니다.
- 통합 테스트 증빙 이미지를 추가했습니다.
    - Swagger 테스트 데이터 생성 화면
    - Swagger API 조회 결과 화면
    - 프론트엔드 대시보드 API 연동 화면
    - 프론트엔드 상세 페이지 API 연동 화면

## 주요 변경 파일

- `docs/12_프론트엔드_백엔드_API연동_테스트_문서.md`
    - 프론트엔드-백엔드 API 연동 테스트 완료 문서
    - 테스트 환경, 테스트 데이터 생성 순서, REST API 조회 결과, 화면 연동 확인 결과 정리
    - WebSocket, error, empty, loading 상태 등 후속 확인 필요 항목 기록
- `frontend/docs/API연동back-front통합테스트정리.md`
    - 프론트엔드 문서 영역에서 확인할 수 있는 통합 테스트 결과 정리본
- `frontend/docs/front-back-integration-test-guideline.md`
    - 통합 테스트 실행 가이드라인 보강
    - Python 3.12, Conda 환경, Swagger 테스트 흐름, 체크리스트 표 정리
- `frontend/.env.example`
    - 로컬 프론트엔드에서 백엔드 API를 바라보기 위한 `NEXT_PUBLIC_API_BASE_URL` 예시 추가
- `frontend/docs/images/swagger-create-test-data.png`
    - Swagger 테스트 데이터 생성 증빙 이미지
- `frontend/docs/images/swagger-create-test-data-1.png`
    - Swagger 테스트 데이터 생성 추가 증빙 이미지
- `frontend/docs/images/swagger-get-api-result.png`
    - Swagger REST API 조회 결과 증빙 이미지
- `frontend/docs/images/frontend-dashboard-api-connected.png`
    - 대시보드 화면의 API 연동 확인 증빙 이미지
- `frontend/docs/images/frontend-detail-api-connected.png`
    - 상세 페이지 화면의 API 연동 확인 증빙 이미지

## 스크린샷 / 테스트 결과

| 구분 | 테스트 항목 | 결과 | 비고 |
|---|---|---|---|
| DB | DB 실행 결과 | 통과 | 테스트 진행 가능 상태 확인 |
| Migration | `alembic upgrade head` | 통과 | 마이그레이션 적용 후 테스트 진행 |
| Backend | FastAPI 서버 실행 | 통과 | `http://localhost:8000` 기준 |
| Frontend | Next.js 서버 실행 | 통과 | `http://localhost:3000` 기준 |
| Create API | `POST /api/drains` | 통과 | Swagger 기준 테스트 데이터 생성 |
| Create API | `POST /api/sensor-data` | 통과 | Swagger 기준 테스트 데이터 생성 |
| Create API | `POST /api/analysis/yolo` | 통과 | Swagger 기준 테스트 데이터 생성 |
| Create API | `POST /api/analysis/xgboost` | 통과 | Swagger 기준 테스트 데이터 생성 |
| Read API | `GET /api/drains` | 통과 | 시설 목록 조회 확인 |
| Read API | `GET /api/drains/{drain_id}` | 통과 | 시설 상세 조회 확인 |
| Read API | `GET /api/drains/{drain_id}/sensors` | 통과 | 센서 데이터 조회 확인 |
| Read API | `GET /api/drains/{drain_id}/risk-history` | 통과 | 위험도 이력 조회 확인 |
| Read API | `GET /api/drains/{drain_id}/analysis/latest` | 통과 | 최신 분석 결과 조회 확인 |
| Read API | `GET /api/dashboard/summary` | 통과 | 대시보드 요약 조회 확인 |
| 화면 | 대시보드 API 연동 확인 | 통과 | 실제 API 데이터 표시 확인 |
| 화면 | 상세 페이지 API 연동 확인 | 통과 | 상세/센서/위험도/분석 결과 표시 확인 |
| WebSocket | `ws://localhost:8000/ws/drains/status` | 제외 | 프론트엔드 WebSocket 수신 기능 미구현 |
| Error Case | 에러 응답 테스트 | 확인 필요 | 정상 연동 테스트 우선 진행 |

## 비고

- 이번 PR은 `feature/frontend`에서 분기한 문서 보강 브랜치 기준으로 작성했습니다.
- 기능 코드 변경은 포함하지 않고, 통합 테스트 결과 문서와 증빙 이미지 추가에 초점을 둡니다.
- WebSocket 연동 테스트는 현재 프론트엔드 수신 기능이 없어 이번 범위에서 제외했습니다.
- API 실패, 존재하지 않는 drain 접근, empty/loading/error 상태는 후속 테스트에서 추가 확인이 필요합니다.
- 테스트 자동화는 아직 포함되지 않았으며, 이후 Playwright 또는 API 테스트 자동화를 별도 작업으로 검토할 수 있습니다.
