## PR 제목

[fix] 배수 시설 상세 페이지 로딩 멈춤 안정화

## 작업 내용

- `/drains/[id]` 상세 페이지에서 route param `id`를 `drainId`로 정규화해 상세 조회, 목록 매칭, 실시간 이벤트 조회에 일관되게 사용했습니다.
- WebSocket 실시간 이벤트 병합 함수가 최초 상세 API 요청을 무효화하지 않도록 `detailRequestIdRef` 증가를 제거했습니다.
- socket 재연결 시 상세 재조회가 최초 로딩 요청을 취소하지 않도록, request id 대신 현재 `drainId` 일치 여부로 늦은 응답을 방어했습니다.
- 현재 URL의 `drainId`와 일치하는 상세 데이터, 오류, not found 상태만 렌더링하도록 정리했습니다.
- 시나리오 실행 중 관리자가 상세 페이지로 이동해도 상세 API 응답이 먼저 화면을 세우고, 이후 실시간 이벤트가 보강 반영되도록 했습니다.

## 주요 변경 파일

| 구분 | 파일 |
| --- | --- |
| 상세 페이지 로딩 안정화 | `frontend/app/drains/[id]/page.tsx` |
| 계획 문서 | `frontend/docs/plans/plan-31-detail-page-loading-stabilization.md` |
| 작업 기록 | `frontend/docs/steps/step-47-detail-page-loading-stabilization.md` |

## 검증 결과

- `npm.cmd run lint` 통과
  - 기존 `frontend/components/fallback-image.tsx`의 native `<img>` 경고 1건 유지
- `npm.cmd run build` 통과
  - `/drains/[id]` dynamic route 빌드 확인

## 리뷰 포인트

- `/demo-control` 자동 시나리오 실행 중 `/`에서 `/drains/DR-004`로 이동해도 로딩 화면에 멈추지 않는지 확인합니다.
- 상세 화면 진입 직후 WebSocket 이벤트가 들어와도 상세 API 응답이 폐기되지 않는지 확인합니다.
- 상세 페이지 간 이동 시 이전 상세 데이터나 오류 상태가 현재 URL에 섞이지 않는지 확인합니다.
- 잘못된 drain id 접근 시 무한 로딩이 아니라 not found 또는 오류 화면으로 빠지는지 확인합니다.

## 비고

- 이번 수정은 `/frontend` 내부로만 제한했습니다.
- `step-46-presentation-demo-control-usage-guideline.md`의 기존 미커밋 변경은 건드리지 않았습니다.
- 실제 브라우저 수동 확인은 발표 리허설 환경에서 시나리오를 켠 상태로 한 번 더 진행하는 것을 권장합니다.
