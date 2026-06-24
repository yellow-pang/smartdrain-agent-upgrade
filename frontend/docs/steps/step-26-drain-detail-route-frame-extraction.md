# 26 상세 route 공통 프레임 분리 결과

## 작업 목표

`app/drains/[id]/page.tsx`의 로딩·오류·정상 화면에 반복되던 AppHeader, 최대 너비 컨테이너, 대시보드 복귀 링크, 상세 제목 영역을 분리했다. 상세 데이터 요청과 WebSocket 이벤트 병합은 기능 회귀 위험이 크므로 이번 단위에서는 route에 유지했다.

## 변경 내용

| 구분 | 변경 전 | 변경 후 |
| --- | --- | --- |
| 공통 화면 컨테이너 | 정상·로딩·오류 화면마다 중복 | `DrainDetailPageFrame`으로 통일 |
| 페이지 제목/복귀 링크 | 정상 화면 route JSX 내부 | `DrainDetailPageHeader`로 분리 |
| 로딩 상태 | route 내부 `DetailLoadingState` | `DrainDetailLoadingPage`로 분리 |
| 오류 상태 | route 내부 `DetailErrorState` | `DrainDetailErrorPage`로 분리 |

새 컴포넌트는 `components/drain-detail/drain-detail-page-frame.tsx`에 둔다. route는 정상 화면에서 frame과 header를 조합하고, 로딩·오류 상황에서는 각각의 상태 페이지를 반환한다.

## 유지한 동작

- `params.id` 해석, 상세 API 요청, 요청 순서 ID 보호 로직을 유지한다.
- 상태·YOLO·XGBoost WebSocket 이벤트를 상세 데이터에 병합하는 기존 effect와 helper를 유지한다.
- API 오류 문구, 대시보드 복귀 링크, 정상 화면의 제목·시설 ID·주소·API 데이터 표시는 동일하다.
- `notFound()` 처리, 센서 요약 fallback, 지도·차트·분석·이력 패널의 데이터 전달은 변경하지 않았다.

## 검증 결과

| 명령어 | 결과 | 비고 |
| --- | --- | --- |
| `pnpm.cmd lint` | 통과 | 오류 0건, 기존 `components/fallback-image.tsx`의 `<img>` 경고 1건 유지 |
| `pnpm.cmd build` | 통과 | Next.js production build 성공. `/` 정적 생성 및 `/drains/[id]` 동적 route 확인 |

## 남은 리스크와 다음 단위

브라우저 수동 점검은 아직 실행하지 않았다. 다음 단위 또는 통합 점검에서 정상 상세, API 실패, 존재하지 않는 ID, WebSocket 상태·YOLO·XGBoost 이벤트 뒤 제목·요약·패널 갱신을 확인한다.

상세 route는 아직 분석 요약, AI 탭, 시설 정보, 위험 이력 등의 표시 컴포넌트를 내부에 포함한다. 다음 세부 단위에서는 API/실시간 병합 helper를 건드리지 않고, 이 표시 패널을 `components/drain-detail/`로 단계적으로 옮긴다.
