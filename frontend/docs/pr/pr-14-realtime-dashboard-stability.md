# PR 14 실시간 대시보드 상태 안정화

## PR 제목

```text
[feat] 실시간 빗물받이 상태 store 안정화
```

## 작업 내용

- Zustand를 도입해 시설 목록, 선택 시설, WebSocket 연결 상태를 공통 store로 관리한다.
- root에서 WebSocket을 연결하고 대시보드와 상세 화면이 같은 최신 시설 상태를 사용하게 한다.
- 재연결 성공 시 기존 REST 목록/요약 API를 재조회한다.
- WS 이벤트와 REST 재조회 결과를 `updatedAt` 기준으로 병합해 늦은 데이터가 최신 상태를 덮지 않게 한다.
- 자동 mock fallback을 제거하고 오류/placeholder UI를 사용한다.

## 주요 변경 파일

| 파일 | 변경 내용 |
| --- | --- |
| `store/drain-store.ts` | 공통 facility 상태, 선택 ID, socket 상태, 동기화 action |
| `components/realtime-drain-sync.tsx` | 초기 로딩, 단일 WS 연결, 재연결 후 REST 동기화 |
| `app/layout.tsx` | 전역 실시간 동기화 컴포넌트 마운트 |
| `app/page.tsx` | 로컬 state/socket hook을 Zustand selector로 교체 |
| `app/drains/[id]/page.tsx` | shared drain 상태와 분석 이벤트 연결 |
| `lib/websocket/drain-status-socket.ts` | 재연결 성공 콜백 추가 |
| `lib/api/drain-data.ts` | mock fallback 제거 및 API base URL 검증 |

## 검증 결과

| 검증 | 결과 |
| --- | --- |
| `npx tsc --noEmit` | 통과 |
| `npm.cmd run build` | 통과 |
| `npm.cmd run lint` | 오류 없음, 기존 `<img>` warning 1건 |
| `git diff --check` | 통과 |

## 리뷰 포인트

1. `updatedAt` 비교가 늦은 WS 이벤트와 REST 재조회 결과 모두에 적용되는지 확인한다.
2. root `RealtimeDrainSync` 외에 대시보드의 중복 WebSocket 연결이 남지 않았는지 확인한다.
3. API 실패가 mock 데이터 화면으로 전환되지 않고 오류 UI로 표시되는지 확인한다.
4. 상세 화면이 공통 store의 최신 facility 상태를 우선 표시하는지 확인한다.
5. 실제 Backend-AI 환경에서 10개 시설 동시·순차 이벤트와 재연결 수동 검증이 남아 있음을 확인한다.

## 남은 리스크

- 이번 변경 후 실제 서버를 사용한 브라우저 수동 검증은 아직 수행하지 않았다.
- 분석 진행/실패 이벤트와 데모 제어 API는 현재 계약 범위 밖이며 팀 협의가 필요하다.
- TanStack Query, Playwright, 시나리오 데이터는 별도 후속 브랜치에서 도입 여부를 결정한다.
