# 34 WebSocket 런타임 검증 및 S3 이미지 URL 정책 보강

## 작업 목표

코드 재점검에서 확인한 두 가지 견고성 항목을 보강했다.

1. WebSocket 메시지가 TypeScript 타입과 다를 때 화면 상태가 깨질 수 있는 문제
2. 향후 S3 CCTV 이미지 연동을 고려할 때 protocol-relative URL의 동작이 환경별로 달라질 수 있는 문제

## WebSocket 런타임 검증

`parseDrainRealtimeEvent()`는 JSON 파싱 후 메시지 구조와 아래 필드를 확인한다.

| 이벤트 | 필수 검증 |
| --- | --- |
| 공통 | 객체 구조, 비어 있지 않은 `payload.drainId` |
| `DRAIN_STATUS_UPDATED` | `updatedAt`, `riskLevel`이 `good/caution/danger/unknown` 중 하나 |
| `YOLO_RESULT_UPDATED` | `updatedAt`, `analyzedAt`, `yoloStatus`가 `clear/partially_blocked/blocked/unknown` 중 하나 |
| `XGBOOST_RESULT_UPDATED` | `updatedAt`, `evaluatedAt`, `riskLevel`이 허용값 중 하나 |

검증에 실패한 메시지는 연결을 끊지 않고 해당 메시지만 무시한다. 따라서 Query cache와 Zustand store, 지도·목록·상세 화면에 계약 밖 상태값이 전달되지 않는다.

## CCTV/S3 이미지 URL 정책

| 형식 | 정책 |
| --- | --- |
| `https://...` | S3 공개 URL 또는 presigned URL의 권장 표준 |
| `http://...` | 로컬 개발 서버 등 개발 환경에서 허용 |
| `/...`, 상대 경로 | `frontend/public/` 또는 현재 앱에서 제공되는 로컬 자산에 허용 |
| `blob:`, 제한된 raster 이미지 `data:` | 브라우저 미리보기·임시 데이터에 허용 |
| `//host/path` | 차단 — 현재 페이지 프로토콜에 따라 동작이 달라지는 것을 방지 |
| 실행 스킴, SVG를 포함한 허용되지 않은 `data:` | 차단 후 placeholder 표시 |

실제 CCTV 연동은 계속 고도화 범위다. S3 구현 시에는 공개 URL 또는 짧은 만료 시간의 presigned **HTTPS** URL을 사용하고, 접근 권한·보존 기간·CDN 캐시 정책을 별도로 확정한다.

## 검증 결과

| 명령어 | 결과 | 비고 |
| --- | --- | --- |
| `pnpm.cmd lint` | 통과 | 오류 0건, 기존 `FallbackImage`의 `<img>` 경고 1건 유지 |
| `pnpm.cmd build` | 통과 | Next.js production build 성공. `/` 정적 생성 및 `/drains/[id]` 동적 route 확인 |
