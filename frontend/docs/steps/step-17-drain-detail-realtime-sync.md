# 17 배수 시설 상세 화면 실시간 동기화 결과

## 작업 결과

- 전역 store에 시설별 마지막 `DRAIN_STATUS_UPDATED` 이벤트를 보관하도록 추가했다.
- 전역 WebSocket 처리 컴포넌트가 기존 대시보드 목록 캐시 갱신과 함께 상태 이벤트를 store에도 전달하도록 연결했다.
- 상세 페이지는 현재 열어 둔 시설의 상태 이벤트만 받아 `detailData`에 즉시 병합한다.
  - 상태, 막힘률, 수위, 유속, 최종 판단, 최근 시각
  - 센서 차트의 최신 포인트
  - 최신 XGBoost 결과와 위험 이력
- 기존 YOLO/XGBoost 개별 이벤트 병합은 유지했다.
- WebSocket이 재연결되면 상세 데이터를 백그라운드에서 보정 조회한다. 기존 화면을 비우지 않으며, 오래된 요청 응답이 새 이벤트 상태를 덮어쓰지 않도록 요청 순서를 확인한다.

## 변경 파일

| 파일 | 변경 내용 |
| --- | --- |
| `store/drain-store.ts` | 시설별 최종 상태 이벤트 상태와 저장 액션 추가 |
| `components/realtime-drain-sync.tsx` | 수신 상태 이벤트를 목록 캐시와 store에 함께 전달 |
| `app/drains/[id]/page.tsx` | 상태 이벤트의 상세 상태·차트·위험 이력 병합, 재연결 보정 조회 추가 |
| `docs/plans/plan-15-drain-detail-realtime-sync.md` | 프론트 전용 범위와 AI 기반 통합 테스트 기준 기록 |

## 검증 결과

| 검증 | 결과 | 비고 |
| --- | --- | --- |
| `npm.cmd --prefix frontend run lint` | 통과 | 새 error 없음. 기존 `components/fallback-image.tsx`의 native `<img>` warning 1건 유지 |
| `npm.cmd --prefix frontend run build` | 실패 | 코드 진단 이전에 현재 `node_modules`가 `@tanstack/react-query`, `@tanstack/react-query-devtools`, `zustand`를 찾지 못해 중단됨 |
| `git diff --check` | 통과 | 공백 오류 없음 |
| AI 기반 통합 테스트 | 필요 | 실제 WebSocket 이벤트 수신 뒤 상세 수치·차트·이력 갱신을 확인해야 함 |

## 남은 리스크

- `DRAIN_STATUS_UPDATED`에 없는 CCTV 이미지 URL·YOLO 신뢰도는 마지막 정상 값으로 유지된다.
- AI 기반 통합 테스트에서 해당 세부값까지 즉시 갱신해야 한다는 요구가 확인되면, 백엔드 이벤트 payload 보완을 별도 작업으로 결정한다.
- build 실패는 의존성 설치 상태 문제이므로, 정상 의존성이 갖춰진 환경에서 다시 실행해야 한다.

## 제안 커밋 메시지

```text
fix: 상세 화면 실시간 상태 데이터를 동기화

- 상태 이벤트를 상세 화면의 센서 차트와 위험 이력에 즉시 반영한다.
- 소켓 재연결 뒤 상세 데이터를 백그라운드로 보정한다.
```
