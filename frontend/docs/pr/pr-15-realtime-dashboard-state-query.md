# PR 15 실시간 대시보드 Query 상태 전환

## PR 제목

```text
[refactor] 실시간 대시보드 서버 상태를 Query cache로 전환
```

## 작업 내용

- TanStack Query를 도입하되 기존 Axios API 함수는 유지했다.
- 시설 목록과 대시보드 요약을 Query cache에서 읽도록 전환했다.
- Zustand에서 시설 목록·요약 원본을 제거하고, 선택 시설·상세 패널·WebSocket 연결 메타 상태만 유지하도록 축소했다.
- `DRAIN_STATUS_UPDATED`는 전체 REST 재호출 대신 관련 목록 cache와, 향후 상세 Query가 사용하는 기존 상세 cache만 부분 갱신한다.
- 재연결 성공 시에만 목록·요약 및 열린 상세 query를 최소 invalidate한다.
- Query Devtools는 development 환경에서만 렌더링한다.

## 데이터 흐름

```text
Axios REST 요청 → TanStack Query cache → 대시보드 표시
WebSocket 상태 이벤트 → setQueryData로 해당 drain만 patch
Zustand → 선택 상태와 연결/오류/마지막 수신 시각만 관리
```

## 주요 파일

| 파일 | 변경 이유 |
| --- | --- |
| `components/query-provider.tsx` | 전역 QueryClient와 development 전용 Devtools 제공 |
| `lib/query/drain-query-keys.ts` | 목록·상세·요약 cache key 중앙 관리 |
| `lib/query/drain-queries.ts` | Axios API 함수를 감싸는 목록·요약 Query hook과 상세 전환 기반 제공 |
| `components/realtime-drain-sync.tsx` | WS cache patch 및 재연결 invalidate 처리 |
| `store/drain-store.ts` | 서버 데이터 제거, UI/연결 메타 상태만 유지 |
| `app/page.tsx` | 목록·요약 Query 결과로 기존 UI 표시 |
| `app/drains/[id]/page.tsx` | 공통 시설 목록을 Query에서 조회. 상세 전체 Query 전환은 후속 범위 |

## 검증 결과

| 검증 | 결과 |
| --- | --- |
| `pnpm exec tsc --noEmit` | 통과 |
| `pnpm lint` | 오류 없음. 기존 `<img>` warning 1건 유지 |
| `pnpm build` | 통과 |

## 리뷰 포인트

1. WebSocket 이벤트가 정상 연결 중 `GET /api/drains`를 다시 호출하지 않는지 확인한다.
2. `DRAIN_STATUS_UPDATED`가 cache에 없는 상세 데이터를 새로 만들지 않는지 확인한다.
3. 재연결 시 목록·요약과 열린 상세만 invalidate되는지 확인한다.
4. Devtools가 production build에 포함되지 않는지 확인한다.
5. 컴포넌트 실제 분리와 memoization은 Profiler 측정 뒤 후속 단계에서 진행한다는 범위가 명확한지 확인한다.

## 남은 리스크

- 실제 Backend-AI 환경의 WS 이벤트/재연결 수동 검증이 남아 있다.
- 상세 전체 데이터와 분석 이력(YOLO/XGBoost)의 Query cache 전환, 표시 컴포넌트 실제 이동과 Profiler 기반 최적화는 후속 범위다.
