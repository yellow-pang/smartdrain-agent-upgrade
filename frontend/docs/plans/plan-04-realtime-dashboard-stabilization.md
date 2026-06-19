# 04_realtime dashboard stabilization 계획

## 1. 작업 개요

| 항목 | 내용 |
|---|---|
| 브랜치 | `feat/realtime-dashboard-stabilization` |
| 작업 범위 | `/frontend` 내부 |
| 핵심 목적 | 실시간 갱신 흐름과 MVP 화면 안정화 |
| 제외 범위 | 새 지도 라이브러리 도입, API 명세 전체 재작성, `/frontend` 밖 파일 수정 |
| 주요 작업 | WebSocket/mock 이벤트 처리, 연결 상태 표시, 대시보드 부분 갱신, loading/error/empty 상태 보강, lint/build 점검 |

이번 작업은 기존 REST API 기반 초기 조회 흐름을 유지하면서, 백엔드 WebSocket 이벤트를 프론트엔드 상태에 안전하게 병합하는 데 집중한다.

```text
REST API 초기 조회
→ 대시보드/상세 기본 데이터 표시
→ WebSocket 연결
→ drainId 기준 Sensor / YOLO / Risk / Failed 이벤트 수신
→ 해당 시설만 부분 갱신
→ 지도 마커, 위험 시설 목록, 상세 화면, 연결 상태 UI 반영
```

## 2. 요구 사항 분석

| 구분 | 요구 사항 | 프론트 적용 방향 |
|---|---|---|
| 초기 조회 | 대시보드, 상세, 이력은 REST API로 조회 | 기존 `loadDashboardData`, `loadDrainDetailData` 흐름 유지 |
| 실시간 갱신 | 상태 변경은 WebSocket 이벤트로 수신 | 새 WebSocket client/hook 또는 기존 구조 확장 |
| 이벤트 단위 | Sensor, YOLO, Risk, Failed 이벤트를 분리 | 단일 위험도 이벤트가 아니라 단계별 이벤트 타입 정의 |
| 부분 갱신 | 전체 목록 재조회 대신 `drainId` 기준 갱신 | dashboard state와 detail state에 merge 함수 추가 |
| YOLO 중간 결과 | 최종 위험도 전에도 먼저 화면 반영 | 상세 화면에 YOLO 결과와 `최종 위험도 분석 중` 상태 표시 |
| XGBoost 최종 위험도 | 지도 마커, 위험 목록, 상세 최종 판단 갱신 | 최종 위험도 기준 정렬과 배지 갱신 |
| 실패 처리 | 분석 실패 시 앱 전체가 멈추지 않게 처리 | 기존 정상 데이터 유지, 해당 영역에 실패/판단불가 표시 |
| 연결 상태 | 연결됨, 대기, 재연결, 실패 표시 | 기존 `DrainRealtimeStatus` UI를 실제 연결 상태와 연결 |
| mock 이벤트 | 백엔드 미연결 환경에서도 흐름 확인 | 개발용 mock event generator 또는 mock WebSocket adapter 준비 |
| 검증 | lint/build 점검 | `npm run lint`, `npm run build` 실행 |

## 3. 현재 프론트 구조에서 확인한 차이

| 영역 | 현재 상태 | 계획에 반영할 점 |
|---|---|---|
| API 타입 | `DrainListItemDto`, `DrainDetailDto`, `YoloResultDto`, `XgboostResultDto` 등이 존재 | 이벤트 payload 타입을 추가하고 기존 DTO와 병합할 기준 필요 |
| WebSocket 타입 | `DRAIN_STATUS_UPDATED` 단일 이벤트 타입만 정의되어 있음 | 확정 흐름 기준 이벤트 4종으로 전환 또는 호환 레이어 필요 |
| WebSocket 연결 코드 | `/frontend/lib/ws` 또는 `/frontend/lib/websocket` 구조가 아직 보이지 않음 | 새 client/hook을 만들 가능성이 높음 |
| 대시보드 | REST 조회 후 `dashboardData` state로 지도/목록/패널 표시 | 이벤트 수신 시 state 배열에서 해당 `drainId`만 갱신 |
| 위험 시설 목록 | 연결 상태 chip UI는 있으나 실제 연결 상태와 연결되지 않음 | WebSocket 상태를 `waiting/connected/reconnecting/error`에 매핑 |
| 상세 화면 | 센서 차트, 현재 위험도, YOLO/XGBoost 카드 구조가 있음 | 최신 센서/YOLO/Risk 영역을 분리 갱신하고 이력 차트는 REST 유지 |
| 이미지 표시 | `imageUrl` 기반 `FallbackImage` 표시 구조가 있음 | WebSocket으로 이미지 파일을 받지 않고 URL만 반영 가능 |
| loading/error/empty | 대시보드 목록 중심으로 일부 구현 | 상세 분석 중/실패/이미지 없음/WebSocket 끊김 상태 보강 필요 |

현재 구조상 가장 큰 변경 지점은 `DRAIN_STATUS_UPDATED` 단일 이벤트 중심에서 `SENSOR_DATA_UPDATED`, `YOLO_RESULT_UPDATED`, `RISK_RESULT_UPDATED`, `ANALYSIS_FAILED` 단계별 이벤트 중심으로 바뀌는 부분이다.

## 4. 확정 기준으로 준비할 이벤트 타입

```ts
type WebSocketEventType =
    | "SENSOR_DATA_UPDATED"
    | "YOLO_RESULT_UPDATED"
    | "RISK_RESULT_UPDATED"
    | "ANALYSIS_FAILED";
```

| 이벤트 | 화면 반영 기준 |
|---|---|
| `SENSOR_DATA_UPDATED` | 최신 수위, 유속, 측정 시각 갱신. 센서 이력 차트는 REST 유지 |
| `YOLO_RESULT_UPDATED` | YOLO 결과 카드 즉시 갱신, 이미지 URL 반영, 최종 위험도 미도착 시 분석 중 표시 |
| `RISK_RESULT_UPDATED` | 지도 마커, 위험 시설 목록, 상세 최종 위험도 카드 갱신 |
| `ANALYSIS_FAILED` | 실패 stage에 따라 YOLO 또는 XGBoost 영역에 실패 상태 표시, 기존 데이터 유지 |

## 5. 예상 수정 파일

실제 구현 전 다시 파일을 확인한 뒤 최소 범위로 조정한다.

| 파일/영역 | 예상 작업 |
|---|---|
| `frontend/lib/api/types.ts` | WebSocket 이벤트 타입, 분석 상태 타입, payload 타입 추가 |
| `frontend/lib/api/adapters.ts` | 이벤트 payload를 UI 데이터에 병합하는 helper 추가 |
| `frontend/lib/ws/*` 또는 `frontend/lib/websocket/*` | WebSocket client, reconnect, message parser, mock event source 추가 |
| `frontend/hooks/*` | 대시보드/상세에서 사용할 realtime hook 추가 가능 |
| `frontend/app/page.tsx` | 대시보드 초기 조회 이후 WebSocket 이벤트 수신 및 부분 갱신 |
| `frontend/app/drains/[id]/page.tsx` | 상세 화면 Sensor/YOLO/Risk/Failed 이벤트 반영 |
| `frontend/components/drain-risk-list.tsx` | 연결 상태와 위험도 정렬/표시 보강 |
| `frontend/components/drain-summary-panel.tsx` | 선택 시설 최신 Sensor/YOLO/Risk 표시 보강 |
| `frontend/components/cctv-snapshot-card.tsx` | 이미지 없음/분석 실패/최근 이미지 없음 상태 보강 |
| `frontend/components/status/*` 또는 기존 컴포넌트 | 분석 중, 실패, 판단불가 상태 배지 보강 가능 |
| `frontend/lib/mock-data.ts` 또는 mock API 파일 | mock 이벤트 흐름 확인용 데이터 추가 |

## 6. 구현 단계

| 단계 | 작업 |
|---|---|
| 1 | 백엔드 확정 WebSocket 방식 확인 후 프론트 이벤트 타입 확정 |
| 2 | 기존 REST 초기 조회와 mock fallback이 깨지지 않도록 타입/adapter 보강 |
| 3 | WebSocket client 또는 hook 추가, 연결 상태와 reconnect 상태 관리 |
| 4 | mock 이벤트 source를 추가해 백엔드 미연결 환경에서도 화면 갱신 흐름 확인 |
| 5 | 대시보드에서 `drainId` 기준으로 시설 목록/지도/선택 패널 부분 갱신 |
| 6 | 상세 화면에서 센서 카드, YOLO 카드, XGBoost 카드, 실패 상태를 분리 표시 |
| 7 | loading/error/empty/분석 중/연결 끊김/이미지 없음 상태 점검 |
| 8 | `npm run lint`, `npm run build` 실행 후 결과 기록 |

## 7. 제외할 일

| 제외 항목 | 이유 |
|---|---|
| 새 지도 라이브러리 도입 | 현재 브랜치 목적은 실시간 갱신 안정화이며 Kakao 지도 구조 유지 |
| API 명세 전체 재작성 | 확정된 이벤트 흐름에 필요한 프론트 타입과 문서만 최소 반영 |
| 백엔드 WebSocket 구현 변경 | `/frontend` 밖 수정 금지 |
| DB/AI 서비스 구조 변경 | 프론트는 DB/AI에 직접 접근하지 않음 |
| WebSocket으로 이미지 파일 수신 | 확정 기준은 `imageUrl`만 전달 |
| 센서 이력 전체 WebSocket 수신 | 이력/차트는 REST API 조회 유지 |

## 8. 사용자 확인 필요 항목

아래 항목은 실제 구현 전 확인이 필요하다.

| 확인 항목 | 추천 방향 | 확인이 필요한 이유 |
|---|---|---|
| WebSocket URL | 예: `NEXT_PUBLIC_WS_URL` 또는 API base URL에서 파생 | 현재 프론트에 실제 WebSocket 연결 코드가 없어 접속 주소 기준이 필요 |
| 이벤트 타입명 | 붙여넣은 기준 4종 사용 | 현재 타입은 `DRAIN_STATUS_UPDATED`라서 백엔드 확정명과 다르면 어댑터가 필요 |
| `drainId` 타입 | number 또는 string 중 확정 필요 | 현재 프론트 UI id는 string 형태도 사용하고 있어 비교/병합 기준을 맞춰야 함 |
| payload 필드명 | camelCase 유지 여부 확인 | 현재 프론트 DTO는 camelCase 기준 |
| XGBoost 시간 필드 | `evaluatedAt` 또는 기존 `predictedAt` 중 확정 필요 | 상세 화면 표시와 타입 변환 기준이 달라짐 |
| YOLO 상태 코드 | `clear/partially_blocked/blocked/unknown` 또는 `good/caution/danger/unknown` | 현재 `YoloStatus`와 붙여넣은 예시의 `yoloStatus: caution`이 다름 |
| 연결 실패 정책 | 자동 재연결 횟수/간격 기준 확인 | UI 상태와 네트워크 부하에 영향 |
| mock 이벤트 사용 방식 | 개발 환경에서 기본 활성화 또는 별도 flag 사용 | 백엔드 미연결 상태에서도 시연할지 결정 필요 |

## 9. 새로 정해진 방식 정리본 요청

현재 소켓 연결에 대해 팀 회의 후 확정된 내용이 있다면, 구현 전에 정리본을 추가로 공유받는 것이 좋다.

특히 아래 내용이 있으면 개발 중 이상한 가정을 줄일 수 있다.

| 필요 정보 | 예시 |
|---|---|
| WebSocket endpoint | `/ws/drains/status`, `/ws/realtime`, drain별 room 구독 여부 |
| 인증/헤더 | 토큰 필요 여부, query string 사용 여부 |
| 실제 event envelope | `{ type, drainId, payload }` 구조인지, wrapper가 있는지 |
| drainId 타입 | DB id number인지 표시용 id string인지 |
| 이벤트 순서 보장 | Sensor → YOLO → Risk 순서가 항상 보장되는지 |
| 재연결 후 복구 | 끊겼다가 다시 연결되면 REST 재조회가 필요한지 |
| 실패 이벤트 stage | `YOLO`, `XGBOOST`, `SENSOR` 등 가능한 값 |
| mock 서버/샘플 메시지 | 프론트 단독 테스트에 사용할 수 있는 메시지 |

정리본이 없다면 이 plan의 이벤트 구조를 기준으로 프론트 타입과 mock 이벤트를 먼저 준비하고, 실제 백엔드 연결 시 adapter에서 차이를 흡수하는 방식으로 진행한다.

## 10. 남은 리스크

| 리스크 | 대응 |
|---|---|
| 백엔드 이벤트 명세가 바뀔 가능성 | WebSocket parser와 adapter를 분리해 변경 범위를 줄임 |
| 현재 프론트 id와 백엔드 `drainId` 타입 차이 | 비교용 normalize helper를 둠 |
| YOLO 상태 코드가 위험도 코드와 다를 가능성 | YOLO 표시용 label mapper와 최종 위험도 mapper를 분리 |
| WebSocket 연결 실패 시 화면 혼란 | 연결 상태 chip과 기존 REST 데이터 유지 정책 적용 |
| mock 이벤트가 실제 이벤트와 달라질 가능성 | mock event type을 실제 타입 근처에 두고 샘플 메시지를 문서화 |
| 상세 화면 문자열/표시 품질 이슈 | 실시간 작업 중 깨진 문구가 발견되면 `/frontend` 안에서 별도 보정 가능 여부 확인 |

## 11. 사용자 승인 후 진행 기준

사용자 승인 후 다음 순서로 구현한다.

1. 새로 확정된 WebSocket 방식 정리본이 있으면 먼저 반영한다.
2. 정리본이 없으면 이 문서의 이벤트 4종을 기준으로 구현한다.
3. `/frontend` 내부에서만 타입, adapter, hook/client, 화면 상태를 수정한다.
4. `npm run lint`, `npm run build` 결과를 작업 완료 문서와 최종 보고에 남긴다.

## 12. 추천 커밋 메시지

제목:

```text
docs: 실시간 대시보드 안정화 계획 정리
```

내용:

```text
- 실시간 대시보드 안정화 작업 범위와 제외 범위를 정리한다.
- Sensor, YOLO, Risk, Failed WebSocket 이벤트 반영 계획을 문서화한다.
- 구현 전 확인이 필요한 소켓 endpoint, drainId 타입, payload 필드 기준을 기록한다.
```
