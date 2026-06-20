# 11 실시간 대시보드 상태 안정화 결과

## 변경 내용

- Zustand를 추가하고 `store/drain-store.ts`에서 대시보드 시설 상태, 선택 시설, WebSocket 상태, REST/WS 병합을 관리한다.
- Root layout의 `RealtimeDrainSync`가 WebSocket 연결을 하나로 관리하고, 재연결 성공 시 기존 REST 목록/요약 API로 재동기화한다.
- `updatedAt`이 더 최신인 `DRAIN_STATUS_UPDATED`만 반영하고, REST 재조회도 최신 상태를 덮어쓰지 않도록 merge한다.
- 대시보드는 로컬 상태와 개별 socket hook 대신 Zustand selector를 사용한다.
- 자동 mock fallback을 제거했다. API 오류는 기존 placeholder UI와 재시도 동작으로 표시한다.
- 상세 화면은 공유 store의 최신 시설 상태와 root WebSocket의 YOLO/XGBoost 이벤트를 사용한다.

## 검증

| 명령 | 결과 |
| --- | --- |
| `npx tsc --noEmit` | 통과 |
| `npm.cmd run build` | 통과 |
| `npm.cmd run lint` | 오류 없음. 기존 `FallbackImage`의 `<img>` 경고 1건 유지 |

## 남은 작업

- 실제 서버를 이용한 10개 시설 동시/순차 이벤트와 재연결 수동 검증
- v0 유래 UI 컴포넌트 분리와 TanStack Query 도입 여부는 후속 브랜치에서 검토
- AI 모델·시나리오·데모 제어 API는 팀 협의 후 필요할 때 진행
