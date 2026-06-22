# PR 09 - realtime dashboard stabilization

## PR 제목

```text
[feat] MVP 기준 WebSocket 실시간 상태 갱신 구현
```

## 작업 배경

이번 작업은 SmartDrain MVP 화면에서 “분석 원천 데이터 전체”를 보여주기보다, 관리자에게 필요한 현재 상태를 안정적으로 갱신하는 데 초점을 둔다.

대시보드와 상세 화면은 아래 값을 중심으로 구성한다.

```text
위험도
막힘 정도
수위
유속
최종 판단
최근 업데이트
WebSocket 연결 상태
```

YOLO/XGBoost 원천 데이터와 실패 이벤트는 아직 백엔드 이벤트가 확정되지 않았고, MVP 첫 화면에서는 정보 밀도를 높이는 원인이 되므로 1차 범위에서 제외했다.

## 작업 내용

| 영역 | 내용 |
|---|---|
| WebSocket | `/ws/drains/status` 연결 hook 추가 |
| 이벤트 처리 | `DRAIN_STATUS_UPDATED` 수신 후 `drainId` 기준 부분 갱신 |
| 대시보드 | 지도, 위험 시설 목록, 선택 패널, 요약 데이터를 WebSocket 이벤트로 갱신 |
| 상세 화면 | 현재 상세 시설과 이벤트 `drainId`가 같을 때 현재 위험 상태 갱신 |
| 상세 UI | 별도 `YOLO / XGBoost 분석 결과` 카드 제거 |
| adapter | WebSocket payload를 `DrainFacility` UI 데이터로 병합 |
| type | 백엔드 payload에 맞춰 nullable 필드 대응 |

## 변경 파일

| 파일 | 변경 내용 |
|---|---|
| `frontend/lib/websocket/drain-status-socket.ts` | WebSocket 연결, 재연결, 메시지 파싱 hook 추가 |
| `frontend/lib/api/types.ts` | `DrainStatusUpdatedEventDto` nullable payload 대응 |
| `frontend/lib/api/adapters.ts` | `mergeDrainStatusEventIntoFacility` 추가 |
| `frontend/app/page.tsx` | 대시보드 실시간 부분 갱신 적용 |
| `frontend/app/drains/[id]/page.tsx` | 상세 실시간 갱신 적용, 별도 분석 결과 카드 제거 |
| `frontend/docs/steps/step-05-realtime-dashboard-stabilization.md` | 이번 단계 판단 기준과 후속 테스트 계획 기록 |
| `frontend/docs/pr/pr-09-realtime-dashboard-stabilization.md` | PR 요약 문서 추가 |

## 왜 YOLO/XGBoost 카드를 제거했는가

루트 문서에는 상세 화면에서 YOLO/XGBoost 결과를 확인해야 한다는 흐름이 있다. 하지만 MVP 첫 화면에서는 세부 원천 데이터보다 현재 판단에 필요한 최종 표시값이 더 중요하다.

따라서 이번 작업은 아래처럼 정리했다.

| 원천/중간 데이터 | 1차 MVP 화면 |
|---|---|
| `yoloStatus` | 직접 표시하지 않음 |
| `confidenceScore` | 직접 표시하지 않음 |
| `obstructionRatio` | 막힘 정도로 표시 |
| `riskLevel` | 상태 배지와 지도 마커 색상 |
| `riskScore` | 위험 점수 또는 정렬 기준 |
| `finalDecision` | 판정 결과 |

## 테스트 결과

| 명령어 | 결과 | 비고 |
|---|---|---|
| `npm run lint` | 통과 | 기존 `fallback-image.tsx` `<img>` 경고 1개 |
| `npm run build` | 통과 | Next.js production build 성공 |

## 리뷰 포인트

| 항목 | 확인 내용 |
|---|---|
| WebSocket URL | `NEXT_PUBLIC_API_BASE_URL`에서 `ws://.../ws/drains/status`로 잘 파생되는지 |
| 이벤트 병합 | `payload.drainId`와 REST `id`가 같은 시설만 갱신되는지 |
| 화면 구성 | 상세 화면에서 별도 AI 원천 데이터 카드가 제거되고 현재 상태 중심으로 보이는지 |
| 연결 상태 | 대시보드 위험 시설 목록에서 연결 상태가 자연스럽게 표시되는지 |

## 남은 작업

다음 브랜치에서 실제 백엔드 WebSocket과 연결해 수동 통합 테스트가 필요하다.

추천 브랜치:

```text
test/realtime-websocket-verification
```

주요 확인:

```text
POST /api/analysis/xgboost
→ 백엔드 DRAIN_STATUS_UPDATED broadcast
→ 프론트 WebSocket 수신
→ 지도 / 위험 시설 목록 / 상세 화면 갱신 확인
```

추가로 이미지 URL 기반 표시도 함께 확인한다.

```text
frontend/public/test-snapshots/ 에 테스트 이미지 배치
→ Swagger POST /api/analysis/yolo 의 imageUrl에 /test-snapshots/*.jpg 입력
→ 여러 YOLO 결과 저장
→ 상세 화면 CCTV 이미지 표시 여부 확인
```

## 커밋 메시지

제목:

```text
feat: MVP 기준 WebSocket 실시간 상태 갱신 구현
```

내용:

```text
- /ws/drains/status WebSocket 연결 hook을 추가한다.
- DRAIN_STATUS_UPDATED 이벤트를 drainId 기준으로 대시보드와 상세 화면에 반영한다.
- 상세 화면의 별도 YOLO/XGBoost 결과 카드를 제거하고 현재 위험 상태 중심으로 정리한다.
- WebSocket payload 병합 adapter와 nullable 타입 대응을 추가한다.
```
