# 12 실시간 대시보드 Query 상태 전환 결과

## 변경 내용

- `@tanstack/react-query`와 개발 전용 `@tanstack/react-query-devtools`를 추가했다.
- Query provider를 root layout에 추가하고, Devtools는 development 환경에서만 렌더링한다.
- 목록·상세·요약 query key factory와 Axios API 함수를 호출하는 query hook을 추가했다.
- Zustand store에서 dashboard/drains/summary 원본을 제거하고 선택 시설, 상세 패널, WebSocket 상태·마지막 수신 시각 중심으로 축소했다.
- `DRAIN_STATUS_UPDATED`는 목록 cache와 이미 존재하는 상세 cache만 `setQueryData`로 patch한다.
- 재연결 성공 때만 목록·요약과 열린 상세 query를 invalidate한다.
- 대시보드 전용 컴포넌트 경로를 추가하고 기존 우측 상세 패널 UI를 유지했다.

## 피드백 반영

- 적용: query key factory, 30초 staleTime, window focus 재조회 비활성화, summary 보수적 갱신 정책, 개발 전용 Devtools.
- 제외: WS payload만으로 상세 cache를 새로 만들기, 목록 item마다 별도 query를 만드는 과도한 분할. 현재 10개 시설과 기존 지도 구조에서는 목록 cache 기반이 더 단순하다.

## 검증

| 명령 | 결과 |
| --- | --- |
| `pnpm exec tsc --noEmit` | 통과 |
| `pnpm lint` | 오류 없음, 기존 `FallbackImage`의 `<img>` 경고 1건 |
| `pnpm build` | 통과 |

## 남은 확인

- 실제 Backend-AI 환경에서 WS 이벤트 수신 시 Network 탭으로 목록 REST 재호출이 없는지 확인한다.
- React DevTools Profiler로 목록 item·지도 marker·상세 패널의 실제 렌더링 범위를 확인한다.
