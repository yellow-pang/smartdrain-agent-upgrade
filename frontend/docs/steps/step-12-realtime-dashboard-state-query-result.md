# 12 실시간 대시보드 Query 상태 전환 결과

## 1. 한눈에 보는 변경 목적

이번 작업은 Axios를 없애는 작업이 아니다. Axios는 REST 요청을 계속 담당하고, 그 응답의 cache·loading·error·재조회 시점은 TanStack Query가 담당하도록 책임을 분리했다.

| 구분 | 변경 전 | 변경 후 |
| --- | --- | --- |
| REST 시설 목록/요약 | Zustand `dashboard`에 저장 | TanStack Query cache에 저장 |
| WebSocket 상태 변경 | Zustand의 전체 목록을 재생성 | Query 목록 cache에서 해당 drain만 교체 |
| 선택 시설/연결 상태 | Zustand | Zustand 유지 |
| 재연결 정합성 | store action이 직접 REST 호출 | Query invalidate로 목록·요약·열린 상세만 갱신 |
| 개발 중 cache 확인 | 없음 | development 환경에서만 Query Devtools 표시 |

## 2. 변경 후 데이터 흐름

```text
Dashboard page
  │ useDrainsQuery(), useDashboardSummaryQuery()
  ▼
TanStack Query cache
  ├─ ['drains']                 ← Axios GET /api/drains
  ├─ ['drains', drainId]        ← 상세 Query 전환을 위한 hook/key 기반
  └─ ['dashboard', 'summary']   ← Axios GET /api/dashboard/summary

WebSocket DRAIN_STATUS_UPDATED
  ├─ Zustand: lastMessageAt, connection status 같은 UI/연결 메타 갱신
  └─ Query: ['drains']의 해당 drain만 setQueryData로 patch
      └─ 상세 cache가 이미 있을 때만 ['drains', drainId]도 patch
```

이 구조에서 **대시보드의 시설 목록과 요약** 서버 데이터 기준은 Query cache다. Zustand에 같은 목록을 복사해 두지 않으므로 REST 응답과 WebSocket 이벤트의 원본이 둘로 갈라지는 문제를 줄인다. 다만 상세 페이지 전체 데이터와 YOLO/XGBoost 이벤트 이력은 기존 화면 동작을 보존하기 위해 아직 별도 후속 전환 범위로 남아 있다.

## 3. 파일별 변경 내용과 확인 방법

| 파일 | 변경 내용 | 코드를 볼 때 확인할 지점 |
| --- | --- | --- |
| `components/query-provider.tsx` | `QueryClientProvider`를 만들고 development에서만 Devtools를 렌더링 | `NODE_ENV === 'development'` 조건이 production 화면에 Devtools를 포함하지 않는지 확인 |
| `app/layout.tsx` | 전역 provider 내부에 `RealtimeDrainSync`와 페이지를 배치 | 모든 페이지가 동일 QueryClient를 공유하는지 확인 |
| `lib/query/drain-query-keys.ts` | 목록·상세·요약 query key를 한 곳에서 정의 | 새 query를 추가할 때 문자열 배열을 직접 만들지 않고 `drainQueryKeys`를 사용하는지 확인 |
| `lib/query/drain-queries.ts` | 기존 Axios API 함수를 호출하는 목록/요약 query와 향후 상세 전환용 hook 추가 | `fetchDrains()`와 `fetchDashboardSummary()`가 API 응답 실패를 throw하여 Query error 상태로 전달하는지 확인 |
| `store/drain-store.ts` | dashboard/drains/summary를 제거하고 선택·상세 패널·socket 메타 중심으로 축소 | 목록·요약 원본을 다시 store에 추가하지 않는지 확인. 기존 상세 분석 이벤트 보관은 후속 전환 전 호환 범위임 |
| `components/realtime-drain-sync.tsx` | WS 이벤트를 Query cache patch 및 재연결 invalidate로 전환 | 이벤트마다 `invalidateQueries(['drains'])`를 호출하지 않는지 확인 |
| `app/page.tsx` | 목록·요약을 Query hook으로 읽고 기존 지도/목록/우측 패널 UI 유지 | loading/error/retry가 Query 결과를 사용하고 있는지 확인 |
| `app/drains/[id]/page.tsx` | 공통 시설 목록을 Zustand 대신 목록 Query에서 찾도록 변경 | 상세 페이지가 제거된 `state.dashboard`를 참조하지 않는지 확인. 상세 전체 조회의 Query 전환은 아직 남아 있음 |

## 4. WebSocket 처리 상세

### 4.1 평상시 상태 이벤트

```text
WS 이벤트 수신
  → RealtimeDrainSync.applyStatusEvent()
  → ['drains'] cache 배열을 순회
  → drainId가 같은 시설만 새 객체로 병합
  → Query cache 변경을 구독하는 화면이 갱신
```

`DRAIN_STATUS_UPDATED`에는 상세 화면의 모든 데이터가 들어 있지 않다. 따라서 상세 cache가 없는데 새 cache를 만들지 않으며, 이미 cache가 있는 경우에도 이벤트가 가진 상태 필드만 기존 상세 데이터에 병합한다. 이미지·이력 같은 상세 전용 데이터를 임의로 만들지 않는 것이 핵심이다. 현재 상세 화면은 이 Query 상세 cache를 아직 주 표시 원본으로 사용하지 않으므로, 이 patch 경계는 상세 Query 전환 후에 실제 화면 반영 범위를 다시 검증해야 한다.

React는 cache를 구독하는 부모 컴포넌트도 다시 렌더링할 수 있다. 따라서 이번 구조의 정확한 목표는 “대시보드 전체가 절대 렌더링되지 않음”이 아니라, 서버 데이터와 연결 상태의 구독 경계를 분리하고 이후 Profiler 측정으로 무거운 표시 영역의 갱신 범위를 줄일 기반을 만든 것이다.

### 4.2 재연결 성공

```text
WS 재연결 성공
  → ['drains'] invalidate
  → ['dashboard', 'summary'] invalidate
  → 우측 상세 패널이 열려 있으면 선택 drain의 상세 query도 invalidate
```

끊긴 동안 놓친 이벤트는 재연결 시 REST 재조회로 보정한다. 반대로 정상 연결 중인 이벤트마다 전체 목록 REST 요청을 만들지 않는다.

## 5. Cache 정책

| 항목 | 설정 | 이유 |
| --- | --- | --- |
| `staleTime` | 30초 | WebSocket patch를 우선 사용하고 불필요한 즉시 재조회는 줄임 |
| `refetchOnWindowFocus` | `false` | 관제 화면을 다시 선택할 때 의도하지 않은 목록 재호출을 방지 |
| `retry` | 1회 | 일시적인 API 실패만 짧게 재시도하고 오래 대기하지 않음 |
| summary WS patch | 하지 않음 | 백엔드 집계 규칙을 프론트가 임의로 재현하지 않음 |

## 6. 컴포넌트 경로 정리

`components/dashboard/` 경로를 추가해 대시보드 표시 요소를 단계적으로 모을 기반을 만들었다. 현재는 기존 지도·목록·우측 상세 패널 구현을 재사용하는 adapter/export 경로가 중심이며, 구현 파일을 모두 이동한 상태는 아니다. UI 회귀를 피하기 위해 화면 배치나 색상은 바꾸지 않았고, 서버 상태 전환을 우선했다.

다음 UI 정리 시에는 기존 최상위 컴포넌트 구현을 dashboard 경로로 실제 이동하고, 목록 item/지도 marker의 Profiler 결과를 바탕으로 필요한 곳에만 memoization을 적용한다.

## 7. 피드백 반영 및 제외 사유

| 항목 | 결정 | 이유 |
| --- | --- | --- |
| query key factory | 적용 | key 오타와 cache 중복을 줄임 |
| summary를 WS마다 patch | 제외 | summary API가 목록 단순 count만 제공한다고 가정할 수 없음 |
| 상세 cache가 없을 때 생성 | 제외 | WS payload가 상세 데이터 전체를 갖고 있지 않음 |
| 목록 item별 별도 query | 제외 | 현재 10개 시설과 지도 표시 구조에서는 목록 cache 하나가 더 단순하고 충분 |
| development 전용 Devtools | 적용 | production build/화면에는 노출하지 않고 개발 중 cache를 확인 가능 |

## 8. 검증 결과

| 명령 | 결과 | 비고 |
| --- | --- | --- |
| `pnpm exec tsc --noEmit` | 통과 | TypeScript 타입 검사 완료 |
| `pnpm lint` | 통과 | 기존 `FallbackImage`의 `<img>` 경고 1건은 유지 |
| `pnpm build` | 통과 | production build와 정적 페이지 생성 완료 |

## 9. 실제 서버에서 확인할 순서

1. `pnpm dev`로 화면을 열고 Query Devtools에서 `['drains']`, `['dashboard', 'summary']` cache가 생성되는지 확인한다.
2. Network 탭에서 최초 진입 시 목록·요약 API가 호출되는지 확인한다.
3. 백엔드에서 `DRAIN_STATUS_UPDATED`를 발생시킨 뒤, Network 탭에 새 `GET /api/drains`가 생기지 않는지 확인한다.
4. 지도 마커·위험 목록·선택된 우측 패널의 해당 시설 값만 최신 값으로 바뀌는지 확인한다.
5. WebSocket을 끊었다가 다시 연결해 목록·요약 요청이 한 번씩만 발생하는지 확인한다. 상세 패널이 열려 있으면 선택 시설 상세 요청도 한 번 발생하는지 확인한다.

## 10. 코드 리뷰 체크리스트

| 확인 항목 | 확인 기준 |
| --- | --- |
| QueryClient 생성 | `QueryProvider`가 `useState(() => new QueryClient())`로 cache를 안정적으로 한 번만 만든다. |
| Devtools 노출 | development 조건 렌더링이며 production build 화면에는 표시하지 않는다. |
| cache patch 불변성 | `setQueryData`가 기존 배열/객체를 직접 수정하지 않고 새 배열·객체를 반환한다. |
| query key 일관성 | 목록·상세·요약 key는 `drainQueryKeys`로만 참조한다. |
| 정상 연결 중 네트워크 | WS 이벤트 수신만으로 목록 REST 요청이 추가되지 않는다. |
| 재연결 네트워크 | 재연결 1회당 목록·요약 요청이 각각 한 번씩만 발생한다. |

## 11. 자동 선택 UX 회귀 추적과 수정

### 11.1 증상

목록과 요약 API가 정상으로 도착해도 첫 진입 또는 새로고침 직후 우측 패널에 다음 오류 안내가 표시될 수 있었다.

```text
상세 정보를 불러올 수 없습니다.
백엔드 연결을 확인한 뒤 다시 시도해주세요.
```

이 문구는 실제 백엔드 연결 실패가 아니라, 선택된 시설 ID가 없는 상태에서 시설 목록만 정상 로드된 경우에도 표시돼 UX를 떨어뜨렸다. 목록과 요약은 독립 API이므로, 요약 API만 지연되거나 실패해도 목록의 자동 선택과 위험 시설 표시는 유지하도록 로딩 경계도 분리했다.

### 11.2 원인

선행 Zustand 구현의 `initializeDashboard()`는 목록을 처음 불러온 뒤 `selectedDrainId`가 없으면 위험도 정렬 목록의 첫 시설을 자동 선택했다. Query 전환 과정에서 목록 원본을 store에서 제거하면서 이 초기 선택 로직도 함께 제거됐고, `app/page.tsx`에는 같은 대체 동작이 없었다.

```text
변경 전: 초기 REST 로드 → store가 첫 시설 ID 선택
변경 직후: Query 목록 로드 → selectedDrainId는 null 유지 → 오류 placeholder 표시
수정 후: Query 목록 로드 → 첫 시설을 화면 기준으로 즉시 사용 → effect로 store 선택 상태 동기화
```

### 11.3 수정 방식

`app/page.tsx`는 위험도 정렬 목록에서 다음 규칙으로 `effectiveSelectedId`를 계산한다.

| 조건 | 선택 결과 |
| --- | --- |
| 사용자가 선택한 ID가 현재 목록에 존재 | 기존 선택 유지 |
| 선택 ID가 없거나 목록 갱신으로 사라짐 | 정렬 목록의 첫 번째 시설 자동 선택 |
| 목록이 비어 있음 | 선택 없음, 빈/오류 상태 표시 |

화면은 `effectiveSelectedId`를 바로 사용하므로 effect가 실행되기 전에도 첫 시설의 지도 마커·목록 항목·우측 패널이 일관되게 표시된다. 이어서 effect가 Zustand의 `selectedDrainId`를 같은 값으로 동기화한다. 따라서 정상 목록이 있는데도 연결 오류 문구가 잠깐 보이는 현상을 막는다.

### 11.4 확인 방법

1. 브라우저 새로고침 후 목록이 하나 이상이면 위험도순 첫 시설이 지도·목록·우측 상세 패널에서 선택되는지 확인한다.
2. 목록의 다른 시설을 클릭한 뒤 WebSocket 갱신 또는 refetch가 발생해도 해당 ID가 목록에 남아 있으면 선택이 유지되는지 확인한다.
3. 선택 시설이 목록에서 사라지는 응답을 받으면 첫 시설로 안전하게 이동하는지 확인한다.
4. 목록이 실제로 비어 있거나 API가 실패한 경우에만 빈 상태 또는 오류 상태가 표시되는지 확인한다.

## 12. 남은 작업과 리스크

- 실제 Backend-AI 환경에서 WS 이벤트 수신과 재연결을 아직 브라우저로 수동 검증하지 않았다.
- 상세 페이지 전체 데이터와 분석 이력(YOLO/XGBoost)의 Query 전환·cache patch 범위는 현재 API 계약을 다시 확인한 뒤 별도 단계로 확장한다.
- 실제 표시 컴포넌트의 dashboard 경로 이동과 React DevTools Profiler 기반 memoization 판단이 남아 있다.
