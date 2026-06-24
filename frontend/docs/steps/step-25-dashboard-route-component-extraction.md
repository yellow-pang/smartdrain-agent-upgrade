# 25 대시보드 route 컴포넌트 분리 결과

## 작업 목표

`app/page.tsx`에 함께 있던 대시보드 요약 상태, 모바일 선택 시설 요약, 지도·위험 목록·상세 패널 레이아웃을 역할별 dashboard 컴포넌트로 분리했다. Query, 선택 상태, WebSocket 갱신 경계는 기존 route에 유지해 화면 기능을 바꾸지 않는 구조 개선에 집중했다.

## 변경 결과

| 구분 | 변경 전 | 변경 후 |
| --- | --- | --- |
| route 책임 | data query, 선택 보정, 요약 표시, 로딩/오류 상태, 모바일 요약, 전체 레이아웃을 한 파일에서 처리 | query·선택 보정·파생 데이터·상태 결정만 처리 |
| 요약 영역 | `page.tsx` 내부 컴포넌트 | `components/dashboard/dashboard-summary-section.tsx` |
| 모바일 요약 | `page.tsx` 내부 memo 컴포넌트 | `components/dashboard/mobile-drain-inline-summary.tsx` |
| 지도/목록/상세 배치 | `page.tsx` JSX | `components/dashboard/dashboard-main-content.tsx` |
| 재시도 callback | 렌더링마다 새 함수 생성 가능 | query의 `refetch` 함수 기준 `useCallback`으로 안정화 |

## 유지한 데이터·상태 경계

```text
DashboardPage
  -> useDrainsQuery / useDashboardSummaryQuery
  -> useDrainStore(selectedDrainId, selectDrain, socketStatus)
  -> 목록 위험도 정렬 및 선택 ID fallback
  -> DashboardSummarySection / DashboardMainContent에 표시용 props 전달

RealtimeDrainSync
  -> 기존처럼 TanStack Query cache와 Zustand store를 갱신
```

- 지도에는 기존과 같이 **정렬 전** 시설 배열을 전달한다.
- 위험 목록에는 기존처럼 위험도순 정렬 배열을 전달한다.
- 목록에 없는 선택 ID는 기존과 같이 첫 시설 또는 `null`로 보정한다.
- 목록 로딩·오류·빈 상태와 요약 API의 로딩·오류·재시도 상태는 기존 조건을 유지한다.
- 위험도 상태 코드와 색상 체계, 반응형 breakpoint, 상세 페이지 링크는 변경하지 않았다.

## 변경 파일

| 파일 | 변경 내용 |
| --- | --- |
| `app/page.tsx` | route를 데이터·상태 조합 역할로 축소하고 안정적인 재시도 callback을 적용 |
| `components/dashboard/dashboard-summary-section.tsx` | 대시보드 요약, skeleton, 오류·재시도 UI 분리 |
| `components/dashboard/mobile-drain-inline-summary.tsx` | 모바일/태블릿 선택 시설 요약과 상세 링크 분리 |
| `components/dashboard/dashboard-main-content.tsx` | 지도, 위험 목록, 모바일 요약, 데스크톱 상세 패널의 반응형 레이아웃 분리 |

## 검증 결과

| 검증 | 결과 | 비고 |
| --- | --- | --- |
| `pnpm.cmd lint` | 통과 | 오류 0건. 기존 `components/fallback-image.tsx`의 `<img>` 경고 1건 유지 |
| `pnpm.cmd build` | 통과 | Next.js production build 성공. `/` 정적 생성, `/drains/[id]` 동적 route 확인 |
| `git diff --check` | 다음 최종 점검에서 실행 | 공백 오류 확인 예정 |

## 남은 수동 확인

브라우저 개발 서버 수동 점검은 이번 작업 환경에서 수행하지 않았다. 다음 단계 착수 전 또는 통합 검증 단계에서 아래를 확인한다.

1. 지도와 위험 목록 선택이 같은 시설의 모바일 요약·데스크톱 상세 패널에 반영되는지 확인한다.
2. 새로고침·목록 오류·빈 목록에서 지도 loading 영역, 목록 상태, 요약 재시도 버튼이 기존과 같은지 확인한다.
3. 360px, 768px, 1280px에서 모바일 요약과 데스크톱 상세 패널의 전환 및 텍스트 겹침이 없는지 확인한다.
4. WebSocket 이벤트 뒤 정렬 순서, 선택 시설, 상세 표시가 일관되게 갱신되는지 확인한다.

## 다음 단계

다음은 2단계인 상세 route 분리다. `app/drains/[id]/page.tsx`의 route parameter 처리, query 상태, 시설 요약·센서·분석·이력 표시를 역할별로 나누되 API DTO와 WebSocket 병합 흐름은 유지한다.
