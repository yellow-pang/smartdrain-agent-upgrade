# 10 실시간 대시보드 서버 상태 Query 전환 및 표시 컴포넌트 분리 계획

## 1. 작업 개요

| 항목 | 내용 |
| --- | --- |
| 현재 브랜치 | `refactor/realtime-dashboard-state-query` |
| 작업 범위 | `/frontend` 내부 대시보드 표시 컴포넌트 분리, Zustand 실시간 메타 상태 정리, TanStack Query 서버 상태 cache 도입 |
| 선행 작업 | `feature/realtime-drain-store-hardening` 완료. 결과는 `docs/steps/step-11-realtime-dashboard-stability-result.md`, PR 요약은 `docs/pr/pr-14-realtime-dashboard-stability.md` 참고 |
| 대상 API | `GET /api/drains`, `GET /api/drains/:id`, `GET /api/dashboard/summary` |
| 대상 WebSocket | `ws://localhost:8000/ws/drains/status`의 `DRAIN_STATUS_UPDATED` |
| 목표 | REST 서버 상태는 TanStack Query cache를 단일 표시 기준으로 두고, WebSocket 수신은 관련 cache만 patch하여 대시보드의 불필요한 전체 갱신과 REST 재호출을 줄인다. |

## 2. 작업 전 확인 결과

| 확인 항목 | 현재 구현 상태 | 이번 브랜치의 처리 방향 |
| --- | --- | --- |
| 대시보드 구성 | `app/page.tsx`가 지도, 목록, 요약, 선택 시설 표시를 직접 조합한다. 표시 컴포넌트는 `components/` 최상위에 흩어져 있다. | 기존 UI와 색상을 유지하면서 `components/dashboard/` 아래의 Shell, Map, 목록, 목록 item, 요약, 연결 상태, 상세 패널 책임으로 분리한다. |
| 서버 상태 | Zustand의 `dashboard`에 drains, 정렬 목록, 요약을 함께 저장하며 REST/WS 병합을 수행한다. | 목록·상세·요약은 TanStack Query cache를 표시 기준으로 사용한다. Zustand에는 drains 원본을 저장하지 않는다. |
| 실시간 메타 상태 | `selectedDrainId`, socket 상태, 마지막 동기화 시각과 drains 데이터가 한 store에 공존한다. | 연결 상태, 재연결 여부, 마지막 수신 시각, 마지막 오류, 선택 drain ID, 상세 패널 열림 여부만 Zustand에 둔다. |
| WebSocket 반영 | `RealtimeDrainSync`가 store action을 호출하고, status 이벤트는 `dashboard.drains` 전체 배열과 정렬/요약을 다시 만든다. | `DRAIN_STATUS_UPDATED`는 `queryClient.setQueryData`로 목록 cache의 해당 drain과 이미 열린 상세 cache만 patch한다. 이벤트마다 전체 REST 재호출은 하지 않는다. |
| 렌더링 경계 | 페이지가 `dashboard` 객체 전체를 구독하므로 drain 1건 변경 때 지도·목록·요약·선택 패널이 함께 갱신될 여지가 있다. | 반복 항목과 marker는 안정된 props 및 `React.memo` 적용을 검토하고, 선택/연결 상태는 각각 selector로 구독한다. callback은 필요한 범위에서 `useCallback`으로 안정화한다. |
| TanStack Query | 아직 설치되어 있지 않다. | 새 의존성 설치와 서버 상태 관리 방식 변경 승인 후 도입한다. Query Devtools는 개발 의존성 추가 승인 시에만 별도로 검토한다. |

## 3. 상태 책임과 데이터 흐름

### 3.1 상태 책임

| 영역 | 책임 |
| --- | --- |
| TanStack Query | REST 목록·상세·요약 cache, loading/error/refetch, 화면 표시의 서버 상태 기준 |
| Zustand | WebSocket connection status, reconnecting, lastMessageAt, lastError, selectedDrainId, detail panel open 여부 |
| WebSocket | `DRAIN_STATUS_UPDATED` 수신, Query cache의 관련 시설 patch, 재연결 성공 시 최소 invalidate/refetch |

### 3.2 목표 데이터 흐름과 cache patch 경계

```text
REST GET /api/drains, /api/drains/:id, /api/dashboard/summary
  → TanStack Query cache (화면 표시의 유일한 서버 상태 기준)

WebSocket DRAIN_STATUS_UPDATED
  → queryClient.setQueryData(["drains"], 목록의 해당 drain만 patch)
  → queryClient.setQueryData(["drains", drainId], cache가 있을 때만 patch)
  → summary cache는 patch 가능한 계약이 확정된 경우에만 계산 갱신,
     그렇지 않으면 재연결 성공 시 최소 invalidate/refetch

Zustand
  → connection/reconnecting/lastMessageAt/lastError/selectedDrainId/detailPanelOpen
```

목록 cache key는 `['drains']`, 상세 cache key는 `['drains', drainId]`, 요약 cache key는 `['dashboard', 'summary']`를 기본안으로 둔다. 실제 `lib/api` 응답 형태와 상세 화면의 조회 필요 범위를 확인한 뒤, 동일한 key factory로 고정한다.

`DRAIN_STATUS_UPDATED` payload에 없는 상세 전용 필드는 제거하거나 임의 값으로 만들지 않고, 기존 상세 cache의 해당 필드만 유지한다. 재연결 성공 시에는 목록과 요약만 invalidate/refetch하고, 상세 패널 또는 상세 화면에서 활성화한 drain의 상세 query만 추가 refetch한다.

## 4. 컴포넌트 구조와 리렌더링 기준

권장 파일 구조는 다음과 같다. 기존 우측 `DrainSummaryPanel` 레이아웃을 유지하는 경우, `DrainDetailDrawer`는 새 UI가 아니라 내부 책임을 분리한 상세 패널로 대체할 수 있다.

```text
components/dashboard/
  DashboardShell.tsx
  DrainMapPanel.tsx
  DrainRiskList.tsx
  DrainRiskListItem.tsx
  DrainStatusSummary.tsx
  DrainConnectionStatus.tsx
  DrainDetailPanel.tsx
```

1. Zustand store 전체를 구독하지 않고 필요한 값과 action을 selector로 각각 구독한다.
2. 목록 item과 지도 marker처럼 반복되는 표시 컴포넌트는 props 비교 효과가 있는 경우에만 `React.memo`를 적용한다.
3. memoized child에 전달하는 선택 callback은 필요한 곳에서 `useCallback`으로 안정화한다.
4. 위험도 정렬·요약처럼 목록 cache에서 계산하는 값은 필요할 때만 `useMemo`로 계산하며, cache와 Zustand에 중복 저장하지 않는다.
5. WS 이벤트 1건으로 대시보드 전체가 다시 렌더링되지 않도록 Query observer와 컴포넌트 prop 경계를 확인한다.

## 5. 구현 순서

1. TanStack Query 의존성 설치 승인 후 `QueryClientProvider`, query key와 목록·상세·요약 query hook을 추가한다.
2. `RealtimeDrainSync`의 이벤트 처리 책임을 Query cache patch와 Zustand 실시간 메타 갱신으로 전환한다.
3. `app/page.tsx`의 화면 조합을 `components/dashboard/*`로 옮기고, 기존 UI와 반응형 레이아웃을 유지한다.
4. 목록 item·지도 marker·요약·상세 패널의 props와 구독 범위를 점검하고 필요한 곳만 memoization 한다.
5. 기존 Zustand의 `dashboard`, drains 원본, REST/WS 병합 action을 제거하고 UI/실시간 메타 상태만 남긴다.

## 6. 검증 계획

| 검증 | 기대 결과 |
| --- | --- |
| `pnpm lint` | lint 오류 없이 통과 |
| `pnpm build` | production build 통과 |
| 대시보드 최초 진입 | 목록·요약 REST API가 정상 호출되고 loading/error UI가 유지됨 |
| `DRAIN_STATUS_UPDATED` 수신 | 해당 drain의 목록·지도·열린 상세 표시가 최신 상태로 반영됨 |
| Network 탭 | WS 이벤트마다 `GET /api/drains`가 반복 호출되지 않음 |
| 상세 패널 열기 | 선택 상태와 상세 query가 정상 동작하며 다른 목록 item의 불필요한 갱신을 줄임 |
| 재연결 | 연결 상태 UI가 표시되고 재연결 성공 시 목록·요약 및 활성 상세만 최소 refetch |
| React DevTools Profiler 또는 `console.count` | 특정 drain 갱신 시 관련 item, marker, summary 중심으로 렌더링됨 |

## 7. 코드 수정 전 사용자 확인 필요 항목

사용자가 아래 항목을 모두 승인했다. 구현은 이 결정과 현재 API 계약을 따른다.

1. `@tanstack/react-query`를 추가하고 Axios API 함수는 유지한다. Query가 Axios 함수를 호출하며, 서버 상태는 Query cache를 기준으로 한다.
2. `components/dashboard/`를 만들고 기존 우측 패널과 화면 배치를 유지한다. 새 Drawer UI는 만들지 않는다.
3. `DRAIN_STATUS_UPDATED`는 관련 목록/상세 cache만 patch한다. 재연결 때만 목록·요약 및 열린 상세를 최소 refetch한다.
4. `@tanstack/react-query-devtools`를 개발 의존성으로 추가하고 `NODE_ENV === 'development'`일 때만 렌더링한다.

## 8. 피드백 반영 기준

| 피드백 | 적용 여부 | 결정 |
| --- | --- | --- |
| Query key factory | 적용 | `drainQueryKeys`로 목록·상세·요약 key를 중앙 관리한다. |
| summary WS patch | 보류 | 요약 API의 집계 계약을 임의로 가정하지 않는다. WS 수신에서는 목록만 patch하고 재연결 시에만 요약을 invalidate한다. |
| `staleTime`과 focus refetch | 적용 | 30초 staleTime, `refetchOnWindowFocus: false`, retry 1회로 실시간 patch와 불필요한 재요청을 조율한다. |
| 상세 cache 신규 생성 | 제외 | WS payload가 불완전하므로 기존 cache가 있을 때만 patch한다. |
| 목록 item별 query 분리 | 제외 | 현재 10개 시설 규모와 지도 컴포넌트 구조에서는 목록 query + 안정된 props 경계가 더 단순하고 적절하다. |

## 9. 범위 밖 항목과 리스크

| 항목 | 이번 브랜치 처리 | 후속/확인 |
| --- | --- | --- |
| 백엔드 API 계약 변경 | 하지 않음 | 현재 REST/WS 계약 유지 |
| mock 데이터 | 실제 API 데이터와 혼합하지 않음 | 테스트 격리가 필요하면 별도 E2E/MSW 검토 |
| YOLO/XGBoost 상세 이력 cache | 현재 상세 화면 계약을 확인한 뒤 최소 범위만 전환 | 이력 캐시 정책은 상세 화면 확장 시 별도 설계 |
| Query Devtools | 기본 미도입 | 패키지 추가 승인 시 검토 |
| E2E/Playwright | 도입하지 않음 | 화면 흐름 안정화와 설치 승인 후 별도 브랜치 |

## 10. 추천 커밋 메시지

제목:

```text
docs: 실시간 대시보드 Query 상태 전환 계획 추가
```

내용:

```text
- TanStack Query와 Zustand의 상태 책임 분리 기준을 정의한다.
- WebSocket cache patch와 재연결 최소 refetch 정책을 기록한다.
- 대시보드 표시 컴포넌트 분리 및 사용자 승인 항목을 정리한다.
```
