## PR 제목

[refactor] 프론트엔드 컴포넌트화·성능·URL 입력 경계 보강

## 작업 내용

- 대시보드 route를 데이터 조회·선택 상태 조합과 표시 컴포넌트로 분리했습니다.
- 상세 route를 공통 frame, 분석 요약, AI 탭, 시설/위험 이력, 지도/현재 상태 패널로 분리했습니다.
- 상세 분석 요약은 일반 데스크톱(1024px 이상)에서 4개 핵심 지표를 한 줄로 표시하도록 조정했습니다.
- 시설 ID를 사용하는 상세 링크와 API path를 인코딩하고, 이미지 URL을 내부 경로 또는 `http/https`로 제한했습니다.
- WebSocket 갱신 시 지도와 CCTV 카드가 관련 값이 변경될 때만 다시 렌더링되도록 비교 기준을 추가했습니다.

## 변경 흐름

```text
DashboardPage
  -> query / 선택 상태 / 위험도 정렬
  -> DashboardSummarySection + DashboardMainContent

DrainDetailPage
  -> API 요청 / WebSocket 병합 / 최신 결과 선택
  -> detail frame + analysis summary + AI tabs + status/map + facility/history panels
```

## 주요 변경 파일

| 구분 | 파일 |
| --- | --- |
| 대시보드 분리 | `app/page.tsx`, `components/dashboard/dashboard-*.tsx`, `components/dashboard/mobile-drain-inline-summary.tsx` |
| 상세 화면 분리 | `app/drains/[id]/page.tsx`, `components/drain-detail/*.tsx` |
| URL 경계 보강 | `lib/drain-route.ts`, `lib/api/drains.ts`, `components/fallback-image.tsx` |
| 상세 링크 적용 | `components/app-header.tsx`, `components/dashboard/mobile-drain-inline-summary.tsx`, `components/drain-summary-panel.tsx` |
| 성능 최적화 | `components/cctv-snapshot-card.tsx`, `components/drain-detail/drain-detail-status-panels.tsx` |
| 작업 기록 | `docs/plans/plan-21-*`, `docs/steps/step-24-*` ~ `step-32-*` |

## 검증 결과

- `pnpm.cmd lint` 통과
  - 오류 0건
  - `components/fallback-image.tsx`의 `<img>` 관련 Next.js 성능 경고 1건 유지
- `pnpm.cmd build` 통과
  - `/` 정적 생성
  - `/drains/[id]` 동적 route 확인
- `git diff --check` 통과

## 리뷰 포인트

- 대시보드 선택 ID 보정과 Query/Zustand/WebSocket 경계가 route에 유지되는지 확인합니다.
- 상세 화면에서 최신 YOLO/XGBoost 결과 선택과 실시간 이벤트 병합 규칙이 기존과 같은지 확인합니다.
- 1024px 이상에서 상세 분석 요약 카드가 4열 한 줄로 표시되고, 작은 화면에서 2열/1열로 전환되는지 확인합니다.
- 시설 ID에 공백·예약 문자가 있을 때 상세 링크와 API 요청이 인코딩된 경로로 생성되는지 확인합니다.
- 외부 CCTV 연동은 고도화 범위로 두고, 현재는 앱 내부·상대 경로, `http/https`, `blob:`, 안전한 raster 이미지 data URL이 fallback 이미지 정책과 함께 렌더링되는지 확인합니다.

## 비고

- 브라우저 수동 점검과 React DevTools Profiler 측정은 이 작업 환경에서 실행하지 않았습니다.
- 실제 API에서 예약 문자가 포함된 시설 ID가 decode되어 처리되는지 통합 환경에서 확인해야 합니다. 실제 CCTV/S3 연동은 고도화 단계에서 공개 또는 presigned `https` URL 정책을 확정합니다.
- `<img>`를 `next/image`로 교체하려면 외부 이미지 도메인 설정과 이미지 최적화 비용 정책에 대한 별도 합의가 필요합니다.
