## PR 제목

[docs] # MVP API 명세서 작성 및 통합 기준 반영

## 작업 내용

- SmartDrain MVP 기준 프론트엔드-백엔드 API 명세서를 작성했습니다.
    - 대시보드, 빗물받이 상세 화면, 실시간 위험도 갱신에 필요한 API 계약을 문서화했습니다.
    - REST API로 초기 데이터를 조회하고 WebSocket으로 변경 이벤트를 수신하는 전체 흐름을 정리했습니다.
    - 백엔드가 분석을 수행하고 프론트가 결과를 표시하는 책임 분리를 명확히 했습니다.
- 백엔드와 맞춘 통합 API 기준을 프론트 명세서에 반영했습니다.
    - 백엔드 API 기준 통합 수정본을 참고 문서로 추가했습니다.
    - 통합 수정본의 endpoint, DTO, WebSocket 이벤트, 테스트 기준을 프론트 명세서에 반영했습니다.
    - 이후 API 변경 사항을 명세서 안에서 추적할 수 있도록 변경 이력과 주요 수정 내용을 정리했습니다.
- API 공통 계약을 보강했습니다.
    - API 응답 필드는 camelCase를 사용하고, DB 내부 필드는 snake_case를 유지할 수 있음을 명시했습니다.
    - 공통 응답 wrapper인 `ApiResponse<T>`, `ApiListResponse<T>` 기준을 정리했습니다.
    - 날짜/시간, 위험 점수, 수위, 유속, 막힘률, 위도/경도 단위 기준을 정리했습니다.
- 프론트와 백엔드가 헷갈리기 쉬운 식별자 기준을 명확히 했습니다.
    - REST 응답은 `id`, WebSocket 이벤트는 `payload.drainId`를 사용하는 기준을 명시했습니다.
    - API 응답의 `id`는 프론트 상태 관리용 외부 식별자로 사용하고, 가능하면 `drain_code` 기반 문자열을 권장하도록 정리했습니다.
    - DB 내부 숫자 PK는 백엔드 내부 관계 설정에만 사용하는 방향을 문서화했습니다.
- MVP 연동 API 목록과 상세 명세를 정리했습니다.
    - 빗물받이 목록, 상세, 센서 이력, 위험 이력, 대시보드 요약, 최신 분석 결과 조회 API를 정리했습니다.
    - 위험도 변경 WebSocket endpoint와 `DRAIN_STATUS_UPDATED` 이벤트 구조를 문서화했습니다.
    - 백엔드 테스트 및 데모용 POST API를 일반 프론트 연동 API와 분리했습니다.
    - 기존 endpoint와 통합 명세 endpoint의 호환 기준을 추가했습니다.
- DTO와 상태 코드 기준을 정리했습니다.
    - 위험도 코드는 `good / caution / danger / unknown` 기준으로 정리했습니다.
    - YOLO 상태 코드는 `clear / partially_blocked / blocked / unknown` 기준으로 정리했습니다.
    - `DrainListItemDto`, `DrainDetailDto`, `SensorHistoryDto`, `RiskHistoryDto`, `AnalysisResultDto`, `DashboardSummaryDto` 등 화면 연동에 필요한 DTO를 문서화했습니다.
- 문서에 흐름도와 테스트 기준을 추가했습니다.
    - 시스템 처리 흐름, 프론트 초기 로딩 및 WebSocket 갱신 흐름, 시퀀스 다이어그램을 추가했습니다.
    - FastAPI `/docs` 기준 MVP API 테스트 순서를 정리했습니다.
    - 통합 테스트 에이전트가 확인해야 할 점검 기준을 추가했습니다.
- MVP 프론트 작업 계획 문서에 API 명세 추적 기준을 반영했습니다.
    - API 명세서가 백엔드 API 기준 통합 수정본을 반영해 관리되고 있음을 남겼습니다.
    - 이후 endpoint, DTO, WebSocket 이벤트 변경 시 API 명세서와 작업 계획 문서에 함께 반영하도록 정리했습니다.

## 주요 변경 파일

- `frontend/docs/api-spec/2026-06-18_mvp_api_spec_v1.md`
    - MVP API 명세서 본문 작성
    - REST API, WebSocket, DTO, 에러 응답, 테스트 순서, 후속 변경 관리 기준 추가
    - 백엔드 통합 수정본 기준으로 식별자, 상태 코드, endpoint, DTO 기준 보강
    - 노션/Markdown에서 보기 쉽도록 표와 Mermaid 흐름도 중심으로 정리
- `frontend/docs/api-spec/SmartDrain_API_통합_명세서_수정본.md`
    - 백엔드 API 기준 통합 수정본 원본 문서 추가
    - 프론트 API 명세서 갱신 기준으로 사용
- `frontend/docs/00_mvp_remaining_frontend_plan.md`
    - MVP API 명세서 관리 위치와 변경 추적 기준 반영
    - 백엔드와 합의된 endpoint, DTO, WebSocket 이벤트 변경 사항을 함께 추적하도록 문구 수정
- `frontend/docs/pr/pr-04-mvp-api-spec-v2.md`
    - 현재 브랜치에서 진행된 API 명세서 작성 및 통합 기준 반영 작업을 PR 문서로 기록

## 스크린샷 / 테스트 결과

- 문서 변경 작업이므로 별도 화면 스크린샷은 없습니다.
- 코드 변경이 없으므로 빌드, 린트, 타입 검증은 실행하지 않았습니다.
- 문서 확인을 진행했습니다.
    - API 명세서에 REST API 목록과 상세 명세가 포함되어 있는지 확인했습니다.
    - WebSocket endpoint와 이벤트 payload 기준이 포함되어 있는지 확인했습니다.
    - DTO 상세 정의, 에러 응답 형식, MVP API 테스트 순서가 포함되어 있는지 확인했습니다.
    - 작업 계획 문서에 API 명세서 추적 문구가 반영되어 있는지 확인했습니다.

## 비고

- 이번 PR은 API 연동 코드 구현이 아니라, 백엔드와 프론트엔드가 같은 기준으로 구현하기 위한 문서 정리 작업입니다.
- 다음 프론트 API 연동 작업에서는 이 명세서 기준으로 `frontend/lib/api/types.ts`, `frontend/lib/api/drains.ts`, WebSocket client, adapter를 갱신해야 합니다.
- 실제 FastAPI `/docs` 응답과 문서가 달라질 경우 API 명세서의 변경 이력에 새 버전을 추가하고 프론트 타입과 호출 함수를 함께 수정해야 합니다.
