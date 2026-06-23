## PR 제목

[fix] MVP 센서·위험도 표시 정확성 개선

## 작업 내용

- 백엔드 API 계약에 맞춰 수위는 `cm`, 유속은 `m/s`, 막힘률은 `%`로 통일했습니다.
- 수위 퍼센트·진행 바, 유량(`m³/min`) 표기, 센서별 고정 상태 배지를 제거했습니다.
- 센서 이력을 측정 시각 오름차순으로 정렬하고, 현재 센서값은 `sensorSummary`를 우선 사용하도록 변경했습니다.
- 실제 기간 API 없이 표시되던 24시간·7일 탭, 임의 데이터 축소, 하드코딩 기준선, 최고값 카드를 제거했습니다.
- 위험 점수 UI 대신 최종 상태와 판단 문구를 모바일·태블릿·데스크톱에서 읽기 쉬운 전체 행 영역으로 표시했습니다.
- API DTO의 nullable 값을 반영하고, 상세 API 실패 시 mock fallback 대신 오류 안내 화면을 표시했습니다.

## 변경 파일

| 구분 | 파일 |
| --- | --- |
| 상세 화면 | `app/drains/[id]/page.tsx`, `components/sensor-trend-chart.tsx` |
| 대시보드·패널 | `app/page.tsx`, `components/drain-summary-panel.tsx`, `components/drain-risk-list.tsx` |
| API 변환·타입 | `lib/api/adapters.ts`, `lib/api/types.ts` |
| mock 동기화 | `lib/mock-data.ts`, `lib/api/mock-responses.ts` |
| 작업 기록 | `docs/plans/plan-19-*`, `docs/steps/step-22-*` |

## 스크린샷 / 테스트 결과

- `npm.cmd exec tsc -- --noEmit` 통과
- `npm.cmd run build` 통과
- `npm.cmd run lint` 오류 없음
  - 기존 `components/fallback-image.tsx`의 `<img>` 사용 경고 1건은 이번 변경과 무관하며 유지됩니다.
- `git diff --check` 통과

## 리뷰 포인트

- `sensorSummary`가 있으면 현재값 카드가 이력 배열 순서와 무관하게 summary 값을 사용하는지 확인합니다.
- `sensorSummary`가 없으면 `measuredAt` 오름차순 이력의 마지막 값이 현재값으로 표시되는지 확인합니다.
- API가 `null`을 반환한 경우 수위·유속·막힘률 영역이 `-`로 표시되고, 위험도는 `unknown`으로 안전하게 처리되는지 확인합니다.
- 360px, 768px, 1280px 이상 화면에서 최종 판단 문구가 카드 폭을 넘지 않는지 확인합니다.

## 비고

- 백엔드 endpoint, WebSocket 이벤트 계약, 새 패키지, 라우팅 구조는 변경하지 않았습니다.
- 실제 commit, push, Pull Request 생성은 담당자가 진행합니다.
