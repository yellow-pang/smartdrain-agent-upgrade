## PR 제목

[docs] # MVP API 명세서 v2 반영

## 작업 내용

- SmartDrain MVP API 명세서를 백엔드 API 기준 통합 수정본에 맞춰 v2로 업그레이드했습니다.
  - 기존 프론트 기준 API 명세 초안을 백엔드와 맞춘 통합 명세 기준으로 갱신했습니다.
  - 문서 상단에 v1에서 v2로 변경된 내용을 추적할 수 있도록 변경 이력과 주요 수정 표를 추가했습니다.
  - 백엔드가 구현한 API 기준을 프론트 문서에도 반영해 이후 연동 작업에서 같은 계약을 참조할 수 있도록 정리했습니다.
- 식별자 운영 기준을 명확히 했습니다.
  - REST 응답은 `id`를 사용하고, WebSocket 이벤트는 `payload.drainId`를 사용하는 기준을 명시했습니다.
  - API 응답의 `id`는 프론트 상태 관리용 외부 식별자로 사용하고, 가능하면 `drain_code` 기반 문자열을 권장하도록 정리했습니다.
  - DB 내부 숫자 PK는 백엔드 내부 관계 설정에만 사용하는 방향을 문서화했습니다.
- API 공통 규칙과 DTO 기준을 보강했습니다.
  - API 응답 필드는 camelCase를 사용하고, DB 내부 필드는 snake_case를 유지할 수 있음을 명시했습니다.
  - `obstructionRatio`는 0~1 ratio로 확정했습니다.
  - `YoloStatus` 기준을 `clear / partially_blocked / blocked / unknown`으로 정리했습니다.
  - `DashboardSummaryDto`, `AnalysisResultDto` 등 통합 명세에서 필요한 DTO를 추가했습니다.
- REST API 목록과 상세 명세를 확장했습니다.
  - 구현 상태와 담당을 포함한 API 종합 목록을 추가했습니다.
  - 최신 분석 결과 조회 API `GET /api/drains/{id}/analysis/latest` 상세 명세를 추가했습니다.
  - 백엔드 테스트 및 데모용 POST API를 일반 프론트 연동 API와 분리했습니다.
  - 기존 endpoint와 통합 명세 endpoint의 호환 기준을 추가했습니다.
- WebSocket과 통합 테스트 기준을 보강했습니다.
  - `DRAIN_STATUS_UPDATED` 이벤트 구조와 화면 반영 기준을 유지했습니다.
  - WebSocket 연결 상태 기준을 `connecting / connected / disconnected / reconnecting / error`로 정리했습니다.
  - FastAPI `/docs` 기준 MVP API 테스트 순서와 통합 테스트 점검 항목을 추가했습니다.
- MVP 프론트 작업 계획 문서에 API 명세 추적 상태를 반영했습니다.
  - 최초 v1 초안 작성 이후 백엔드 API 기준 통합 수정본을 반영해 v2로 업그레이드했다는 내용을 남겼습니다.

## 주요 변경 파일

- `frontend/docs/api-spec/2026-06-18_mvp_api_spec_v1.md`
  - 문서 제목과 상태를 `SmartDrain MVP API 명세서 v2` 기준으로 갱신
  - v1 → v2 변경 이력 추가
  - 식별자 운영 기준 추가
  - API 공통 규칙, DTO, REST API, WebSocket, 테스트 기준 확장
  - 노션/Markdown에서 보기 쉽도록 하위 섹션 heading 정리
- `frontend/docs/api-spec/SmartDrain_API_통합_명세서_수정본.md`
  - 백엔드 API 기준 통합 수정본 원본 문서 추가
  - v2 명세서 반영 기준으로 사용
- `frontend/docs/00_mvp_remaining_frontend_plan.md`
  - MVP API 명세가 v2로 업그레이드되었음을 추적 문구에 반영
  - 이후 endpoint, DTO, WebSocket 이벤트 변경 시 API 명세와 작업 계획 문서에 함께 기록하도록 정리

## 스크린샷 / 테스트 결과

- 문서 변경 작업이므로 별도 화면 스크린샷은 없습니다.
- 코드 실행, 빌드, 린트 검증은 진행하지 않았습니다.
- 문서 확인을 진행했습니다.
  - API 명세서 상단 변경 이력 확인
  - 식별자 운영 기준, 최신 분석 API, DTO 상세 정의, MVP API 테스트 순서 포함 여부 확인
  - 작업 계획 문서의 API 명세 추적 문구 확인

## 비고

- 현재 파일명은 기존 추적 경로를 유지하기 위해 `2026-06-18_mvp_api_spec_v1.md`를 그대로 사용하지만, 문서 본문 기준 버전은 v2입니다.
- 다음 프론트 API 연동 작업에서는 이 명세서 기준으로 `frontend/lib/api/types.ts`, `frontend/lib/api/drains.ts`, WebSocket client, adapter를 갱신해야 합니다.
- 실제 FastAPI `/docs` 응답과 다를 경우 API 명세 변경 이력에 v3 항목을 추가하고 프론트 타입과 호출 함수를 함께 수정해야 합니다.
