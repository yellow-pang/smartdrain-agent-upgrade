# 11 실시간 대시보드 상태 안정화 결과

## 변경 내용

- Zustand를 추가하고 `store/drain-store.ts`에서 대시보드 시설 상태, 선택 시설, WebSocket 상태, REST/WS 병합을 관리한다.
- Root layout의 `RealtimeDrainSync`가 WebSocket 연결을 하나로 관리하고, 재연결 성공 시 기존 REST 목록/요약 API로 재동기화한다.
- `updatedAt`이 더 최신인 `DRAIN_STATUS_UPDATED`만 반영하고, REST 재조회도 최신 상태를 덮어쓰지 않도록 merge한다.
- 대시보드는 로컬 상태와 개별 socket hook 대신 Zustand selector를 사용한다.
- 자동 mock fallback을 제거했다. API 오류는 기존 placeholder UI와 재시도 동작으로 표시한다.
- 상세 화면은 공유 store의 최신 시설 상태와 root WebSocket의 YOLO/XGBoost 이벤트를 사용한다.

## 변경 전과 변경 후

| 구분 | 변경 전 | 변경 후 |
| --- | --- | --- |
| 상태 위치 | `app/page.tsx`가 목록, 선택 ID, 로딩, 실시간 갱신을 직접 관리 | Zustand `useDrainStore`가 공통 상태를 관리하고 화면은 selector로 조회 |
| WebSocket | 대시보드와 상세가 각각 socket hook을 호출 | root의 `RealtimeDrainSync`가 연결하고 이벤트를 store에 전달 |
| 재연결 | 3초 후 socket만 다시 연결 | 재연결 성공 후 기존 목록/요약 REST API를 재조회 |
| 최신성 | 수신 순서대로 기존 상태를 덮을 수 있음 | `updatedAt`이 더 최신인 상태 이벤트와 REST 응답만 반영 |
| API 실패 | mock 데이터 화면으로 전환 | 자동 mock fallback 제거, 기존 오류/placeholder UI 표시 |

## 파일별 상세 변경

| 파일 | 구체적인 변경 | 효과 |
| --- | --- | --- |
| `package.json`, lockfiles | `zustand` 의존성 추가 | drain별 selector와 전역 action 사용 가능 |
| `store/drain-store.ts` | dashboard, 선택 ID, socket 상태, `lastSyncedAt`, REST/WS merge action 추가 | 지도·목록·요약·상세가 동일 facility source를 사용 |
| `components/realtime-drain-sync.tsx` | 최초 REST 로딩, 단일 WS 구독, 재연결 후 동기화 연결 | route별 연결 중복을 줄이고 lifecycle을 한 곳에 집중 |
| `app/layout.tsx` | `RealtimeDrainSync` 마운트 | 페이지 이동에도 실시간 연결 흐름 유지 |
| `app/page.tsx` | 로컬 state와 socket hook 제거, Zustand selector와 재시도 action 적용 | 대시보드 UI가 공통 상태를 읽음 |
| `app/drains/[id]/page.tsx` | store의 최신 drain과 YOLO/XGBoost 이벤트를 상세에 연결 | 대시보드와 상세의 현재 상태 불일치 축소 |
| `lib/websocket/drain-status-socket.ts` | `onConnected(reconnected)` 콜백 추가 | 최초 연결과 재연결 성공을 구분해 REST 동기화 실행 |
| `lib/api/drain-data.ts` | mock response 생성/fallback 제거, API base URL 검증 | 장애를 데모 데이터로 숨기지 않음 |

## 데이터 흐름

```text
RootLayout
  → RealtimeDrainSync
    → GET /api/drains + GET /api/dashboard/summary
    → useDrainStore.dashboard 저장
    → WS /ws/drains/status 연결
      → DRAIN_STATUS_UPDATED: updatedAt 비교 후 해당 drain만 merge
      → YOLO_RESULT_UPDATED: drain별 최신 YOLO 이벤트 저장
      → XGBOOST_RESULT_UPDATED: drain별 최신 XGBoost 이벤트 저장
    → 재연결 성공: REST 재조회 후 drain별 시간 비교 merge

DashboardPage / DrainDetailPage
  → 필요한 Zustand selector만 조회
  → 기존 UI 컴포넌트에 표시 데이터 전달
```

## 최신성 규칙

1. 상태 이벤트는 `payload.updatedAt`이 현재 시설의 `updatedAt`보다 새 경우에만 반영한다.
2. 재연결 후 REST 목록도 같은 시간 비교를 거쳐 merge한다.
3. ISO 시간 파싱이 불가능한 값은 최신 상태를 덮지 않는다.
4. YOLO/XGBoost 이벤트는 drain별 최신 이벤트를 보관하고 상세 화면이 이를 반영한다.

## UI 영향

- 지도, 위험 목록, 요약 카드, 상세 화면의 기존 레이아웃과 색상은 유지했다.
- 연결 상태 배지는 store가 제공하는 상태를 계속 사용한다.
- API 실패 시 자동 mock 화면 대신 기존 오류 UI 및 `PlaceholderState`를 사용한다.
- CCTV 이미지 URL 실패 시 기존 `FallbackImage` placeholder 동작은 그대로 유지한다.

## 검증

| 명령 | 결과 |
| --- | --- |
| `npx tsc --noEmit` | 통과 |
| `npm.cmd run build` | 통과 |
| `npm.cmd run lint` | 오류 없음. 기존 `FallbackImage`의 `<img>` 경고 1건 유지 |

## 남은 작업

- 실제 서버를 이용한 10개 시설 동시/순차 이벤트와 재연결 수동 검증
- 상세 API 실패 전용 UI는 후속 UI 정리에서 보강
- v0 유래 UI 컴포넌트 분리와 TanStack Query 도입 여부는 후속 브랜치에서 검토
- AI 모델·시나리오·데모 제어 API는 팀 협의 후 필요할 때 진행

실제 Backend-AI 환경에서의 브라우저 수동 검증은 이번 변경 후 아직 수행하지 않았다.
