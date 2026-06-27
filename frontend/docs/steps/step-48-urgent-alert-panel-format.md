# 48 긴급 알림 패널 웹 표시 개선 결과

## 작업 목표

웹 화면에서 긴급 알림 패널의 줄바꿈, 표시 개수 체감, 최신 알림 위치 문제를 개선했다.

## 변경 내용

| 파일 | 변경 내용 |
| --- | --- |
| `components/app-header.tsx` | 웹 알림 패널 폭을 넓히고 헤더/버튼 줄바꿈을 방지 |
| `components/app-header.tsx` | 알림 목록을 `updatedAt` 기준 최신순으로 정렬 |
| `components/app-header.tsx` | 목록 높이를 `max-h-[min(70vh,34rem)]`로 확장해 4개 이상도 스크롤 확인 가능 |
| `components/app-header.tsx` | 시설명은 한 줄 truncate, 상태 배지는 고정, 메시지는 최대 2줄로 제한 |
| `store/drain-store.ts` | 같은 시설 알림이 갱신되면 기존 위치 유지가 아니라 최신 항목으로 맨 위에 이동 |

## 동시 알림 처리 기준

- 알림은 기존 정책대로 시설별 1건으로 병합한다.
- 여러 시설 알림이 한 번에 들어오면 `updatedAt` 기준 최신순으로 표시한다.
- 같은 시설의 상태가 다시 갱신되면 해당 시설 알림을 최신 내용으로 바꾸고 맨 위로 올린다.
- store에는 최대 20건을 유지하고, 패널에서는 스크롤로 확인한다.

## 검증 결과

| 검증 | 결과 |
| --- | --- |
| `npm.cmd run lint` | 통과. 기존 `components/fallback-image.tsx`의 native `<img>` 경고 1건 유지 |
| `npm.cmd run build` | 통과 |

## 특이사항

첫 `npm.cmd run build`는 `.next/dev/types/routes.d.ts`의 깨진 생성 파일 때문에 실패했다. `.next` 캐시 삭제 후 재실행하니 정상 통과했다.

## 남은 리스크

- 실제 웹 viewport에서 알림 5개 이상이 쌓였을 때 패널 높이가 발표 화면에 맞는지 수동 확인하면 좋다.
- 모바일은 기존처럼 화면 좌우 여백을 쓰는 fixed 패널을 유지한다.
