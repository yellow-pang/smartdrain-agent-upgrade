# 28 상세 시설 정보·위험 이력 패널 분리 결과

## 작업 목표

상세 route 내부의 시설 정보와 과거 위험 이력 표시를 전용 컴포넌트로 분리했다. 상세 API 요청, WebSocket 이벤트 병합, 현재 선택 시설 판단은 route에 유지해 데이터 흐름을 바꾸지 않았다.

## 변경 내용

| 컴포넌트 | 새 위치 | 책임 |
| --- | --- | --- |
| `FacilityInfoCard` | `components/drain-detail/facility-overview-panels.tsx` | 시설 ID·주소·상태·막힘률·수위·유속·최근 업데이트 표시 |
| `RiskHistoryCard` | `components/drain-detail/facility-overview-panels.tsx` | 위험도 이력의 시각, 상태 색상, 상태 배지 표시 |

시설 정보 패널은 `DrainFacility`만 받고 상태 메타를 내부에서 계산한다. 위험 이력 패널은 `RiskHistoryItem[]`만 받아 route의 상세 API/실시간 데이터 구조와 분리했다.

## 유지한 동작

- 위험도별 상태 색상과 배지를 `STATUS_META`, `StatusBadge` 기준으로 유지한다.
- 막힘률은 `%`, 수위는 `cm`, 유속은 `m/s`로 기존 표기를 유지한다.
- 날짜 표시는 기존 `formatDateTimeForDisplay` helper를 사용한다.
- 우측 컬럼의 순서, 카드 스타일, 반응형 layout과 데이터 전달 흐름은 바꾸지 않았다.

## 검증 결과

| 명령어 | 결과 | 비고 |
| --- | --- | --- |
| `pnpm.cmd lint` | 통과 | 오류 0건, 기존 `components/fallback-image.tsx`의 `<img>` 경고 1건 유지 |
| `pnpm.cmd build` | 통과 | Next.js production build 성공. `/` 정적 생성 및 `/drains/[id]` 동적 route 확인 |

## 다음 단계

상세 route에 남은 AI 탭과 분석 이력 표시를 `components/drain-detail/`로 분리한다. 이 단계에서도 API 요청, 최신 결과 선택, WebSocket 병합 helper는 route에 유지한다.
