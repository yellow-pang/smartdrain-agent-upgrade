# 04_realtime dashboard stabilization 계획

## 1. 작업 개요

| 항목 | 내용 |
|---|---|
| 브랜치 | `feat/realtime-dashboard-stabilization` |
| 작업 범위 | `/frontend` 내부 |
| 핵심 목적 | 실시간 갱신 흐름과 MVP 화면 안정화 |
| 제외 범위 | 새 지도 라이브러리 도입, API 명세 전체 재작성, `/frontend` 밖 파일 수정 |
| 주요 작업 | 백엔드 WebSocket 이벤트 처리, 연결 상태 표시, 대시보드 부분 갱신, loading/error/empty 상태 보강, lint/build 점검 |

이번 작업은 기존 REST API 기반 초기 조회 흐름을 유지하면서, 현재 백엔드에 구현된 WebSocket 이벤트를 프론트엔드 상태에 안전하게 병합하는 데 집중한다.

```text
REST API 초기 조회
→ 대시보드/상세 기본 데이터 표시
→ WS /ws/drains/status 연결
→ DRAIN_STATUS_UPDATED 이벤트 수신
→ 해당 시설만 부분 갱신
→ 지도 마커, 위험 시설 목록, 상세 화면, 연결 상태 UI 반영
```

mock 이벤트는 이번 구현 범위에서 제외한다. 백엔드가 실제 WebSocket endpoint를 제공하므로, MVP 프론트는 백엔드에서 내려주는 데이터 기준으로 연결한다.

## 2. 요구 사항 분석

| 구분 | 요구 사항 | 프론트 적용 방향 |
|---|---|---|
| 초기 조회 | 대시보드, 상세, 이력은 REST API로 조회 | 기존 `loadDashboardData`, `loadDrainDetailData` 흐름 유지 |
| 실시간 갱신 | 상태 변경은 WebSocket 이벤트로 수신 | 현재 백엔드의 `/ws/drains/status`에 연결 |
| 이벤트 단위 | WebSocket endpoint는 1개만 사용하고, 메시지 내부 구분자로 이벤트를 나눔 | `/ws/drains/status` 단일 endpoint 유지, `type` 값으로 Sensor/YOLO/Risk/Failed 구분 |
| 부분 갱신 | 전체 목록 재조회 대신 `drainId` 기준 갱신 | dashboard state와 detail state에 merge 함수 추가 |
| YOLO 중간 결과 | 팀 흐름상 YOLO 완료 시 즉시 반영 필요 | 현재 백엔드는 YOLO 생성 시 broadcast가 없어 REST 최신 분석 또는 후속 백엔드 변경 필요 |
| XGBoost 최종 위험도 | 지도 마커, 위험 목록, 상세 최종 판단 갱신 | 현재 백엔드는 XGBoost 생성 후 이벤트 발행 |
| 실패 처리 | 분석 실패 시 앱 전체가 멈추지 않게 처리 | 현재 백엔드는 실패 이벤트가 없어 프론트 연결/파싱 오류와 REST 오류 중심 처리 |
| 상세 화면 구성 | MVP 첫 화면 기준으로 필요한 정보만 표시 | 1차 구현에서는 명시적 YOLO/XGBoost 원천 데이터 노출을 제외하고 현재 위험 상태/시설 정보 중심으로 구성 |
| 연결 상태 | 연결됨, 대기, 재연결, 실패 표시 | 기존 `DrainRealtimeStatus` UI를 실제 연결 상태와 연결 |
| 검증 | lint/build 점검 | `npm run lint`, `npm run build` 실행 |

## 3. 백엔드와 루트 문서 확인 결과

| 확인 위치 | 현재 기준 | 프론트 계획 반영 |
|---|---|---|
| `backend/app/routers/websocket.py` | `WS /ws/drains/status` endpoint 존재 | 이 endpoint로 연결 |
| `backend/app/websocket/manager.py` | 연결 등록, 해제, 전체 broadcast 구현 | 프론트는 단일 broadcast 수신 기준으로 처리 |
| `backend/app/routers/analysis.py` | `POST /api/analysis/xgboost` 후에만 WebSocket broadcast 실행 | MVP 실시간 갱신은 XGBoost 최종 결과 이벤트 중심 |
| `backend/app/routers/analysis.py` | `POST /api/analysis/yolo`는 WebSocket broadcast 없음 | YOLO 즉시 반영은 백엔드 추가 구현 필요 |
| `backend/app/routers/sensor_data.py` | `POST /api/sensor-data`는 WebSocket broadcast 없음 | 센서 즉시 반영은 백엔드 추가 구현 필요 |
| `backend/app/schemas/api_response.py` | 이벤트 payload 생성 함수는 `drain_status_event_payload` | 프론트 타입은 이 payload와 맞춤 |
| `backend/README.md` | WebSocket 이벤트 타입은 `DRAIN_STATUS_UPDATED` | 기존 프론트 타입 유지/보강 |
| `docs/reference/11_API명세서.md` | MVP WebSocket 기준은 `/ws/drains/status`, `DRAIN_STATUS_UPDATED` | 루트 통합 명세 기준과 백엔드 구현이 일치 |
| `docs/legacy-mvp/06_시스템아키텍처.md` | XGBoost 판단 결과 저장 또는 위험도 변경 시 이벤트 발행 | MVP에서는 최종 위험도 이벤트 중심으로 해석 |

현재 백엔드 이벤트 예시는 다음 구조다.

```json
{
  "type": "DRAIN_STATUS_UPDATED",
  "payload": {
    "drainId": "DR-004",
    "riskLevel": "danger",
    "riskScore": 0.91,
    "waterLevelCm": 85,
    "flowVelocityMps": 0.05,
    "obstructionRatio": 0.88,
    "finalDecision": "막힘률과 수위가 높아 침수 위험이 큽니다.",
    "updatedAt": "2026-06-18T09:30:00+09:00"
  }
}
```

## 4. 현재 프론트 구조에서 확인한 차이

| 영역 | 현재 상태 | 계획에 반영할 점 |
|---|---|---|
| API 타입 | `DrainListItemDto`, `DrainDetailDto`, `YoloResultDto`, `XgboostResultDto` 등이 존재 | 이벤트 payload 타입을 추가하고 기존 DTO와 병합할 기준 필요 |
| WebSocket 타입 | `DRAIN_STATUS_UPDATED` 단일 이벤트 타입이 이미 정의되어 있음 | 현재 백엔드와 맞으므로 이 타입을 실제 연결에 사용 |
| WebSocket 연결 코드 | `/frontend/lib/ws` 또는 `/frontend/lib/websocket` 구조가 아직 보이지 않음 | 새 client/hook을 만들 가능성이 높음 |
| 대시보드 | REST 조회 후 `dashboardData` state로 지도/목록/패널 표시 | 이벤트 수신 시 state 배열에서 해당 `drainId`만 갱신 |
| 위험 시설 목록 | 연결 상태 chip UI는 있으나 실제 연결 상태와 연결되지 않음 | WebSocket 상태를 `waiting/connected/reconnecting/error`에 매핑 |
| 상세 화면 | 센서 차트, 현재 위험도, 시설 정보, 위험 이력, 별도 YOLO/XGBoost 카드 구조가 있음 | 1차 MVP에서는 별도 YOLO/XGBoost 카드를 제거하고 WebSocket/REST의 최종 표시값 중심으로 구성 |
| 이미지 표시 | `imageUrl` 기반 `FallbackImage` 표시 구조가 있음 | WebSocket으로 이미지 파일을 받지 않고 URL만 반영 가능 |
| loading/error/empty | 대시보드 목록 중심으로 일부 구현 | 상세 분석 중/실패/이미지 없음/WebSocket 끊김 상태 보강 필요 |

현재 구조상 가장 큰 변경 지점은 WebSocket 타입 자체가 아니라, 정의만 있던 `DRAIN_STATUS_UPDATED` 이벤트를 실제 화면 state 갱신에 연결하는 부분이다.

## 5. MVP 구현 기준 이벤트 타입

팀 합의 방향은 WebSocket endpoint를 여러 개로 나누지 않고, 하나의 endpoint에서 메시지 내부 타입으로 구분하는 방식이다.

```text
WS /ws/drains/status
→ message.type 확인
→ SENSOR_DATA_UPDATED / YOLO_RESULT_UPDATED / RISK_RESULT_UPDATED / ANALYSIS_FAILED / DRAIN_STATUS_UPDATED 중 해당 handler 실행
```

즉, endpoint는 하나이고 프론트는 수신 메시지를 parse한 뒤 `type` 필드로 어떤 데이터를 받았는지 판단한다.

현재 백엔드는 아래 단일 이벤트만 발행한다.

```ts
type DrainStatusUpdatedEventDto = {
    type: "DRAIN_STATUS_UPDATED";
    payload: {
        drainId: string;
        riskLevel: RiskLevel;
        riskScore: number | null;
        waterLevelCm?: number | null;
        flowVelocityMps?: number | null;
        obstructionRatio?: number | null;
        finalDecision?: string | null;
        updatedAt: string;
    };
};
```

추후 팀 흐름을 더 정확히 반영하려면 endpoint를 추가하지 않고 같은 `/ws/drains/status`에서 아래처럼 이벤트 타입만 확장하는 방향이 적절하다.

```ts
type DrainRealtimeEvent =
    | SensorDataUpdatedEventDto
    | YoloResultUpdatedEventDto
    | RiskResultUpdatedEventDto
    | AnalysisFailedEventDto
    | DrainStatusUpdatedEventDto;
```

| 이벤트 타입 | 용도 | 현재 백엔드 구현 여부 |
|---|---|---|
| `SENSOR_DATA_UPDATED` | 센서 수집 후 수위/유속 최신값 전달 | 없음 |
| `YOLO_RESULT_UPDATED` | YOLO 완료 후 이미지 분석 결과 전달 | 없음 |
| `RISK_RESULT_UPDATED` | XGBoost 최종 위험도 전달 | 없음 |
| `ANALYSIS_FAILED` | 센서/YOLO/XGBoost 실패 상태 전달 | 없음 |
| `DRAIN_STATUS_UPDATED` | 최종 상태 요약 전달 | 있음 |

MVP 프론트 구현은 현재 백엔드의 `DRAIN_STATUS_UPDATED`를 먼저 처리하되, WebSocket parser는 endpoint가 하나라는 전제를 유지하고 `type` 기반 분기 구조로 만든다. 이렇게 해두면 백엔드가 이후 단계별 이벤트를 추가해도 endpoint 변경 없이 handler만 확장할 수 있다.

| 필드 | 화면 반영 기준 |
|---|---|
| `drainId` | REST 응답의 `id`와 매칭해 해당 시설만 갱신 |
| `riskLevel` | 지도 마커 색상, 상태 배지, 위험 시설 목록 정렬 |
| `riskScore` | 위험 점수 표시 또는 판단불가 처리 |
| `waterLevelCm` | 최신 수위 표시 |
| `flowVelocityMps` | 최신 유속 표시 |
| `obstructionRatio` | 막힘률 progress 표시 |
| `finalDecision` | 최종 판단 문구 |
| `updatedAt` | 최근 업데이트 시간 |

팀에서 공유한 단계별 흐름은 화면 설계 기준으로 유지하되, 현재 백엔드가 단계별 이벤트를 발행하지 않으므로 MVP 구현은 `DRAIN_STATUS_UPDATED` 단일 이벤트로 최종 상태를 갱신한다.

## 6. 예상 수정 파일

실제 구현 전 다시 파일을 확인한 뒤 최소 범위로 조정한다.

| 파일/영역 | 예상 작업 |
|---|---|
| `frontend/lib/api/types.ts` | 현재 백엔드 payload 기준 WebSocket 이벤트 타입 보강 |
| `frontend/lib/api/adapters.ts` | 이벤트 payload를 UI 데이터에 병합하는 helper 추가 |
| `frontend/lib/websocket/*` | WebSocket client, reconnect, message parser 추가 |
| `frontend/hooks/*` | 대시보드/상세에서 사용할 realtime hook 추가 가능 |
| `frontend/app/page.tsx` | 대시보드 초기 조회 이후 WebSocket 이벤트 수신 및 부분 갱신 |
| `frontend/app/drains/[id]/page.tsx` | 상세 화면 별도 YOLO/XGBoost 결과 카드 제거, 현재 위험 상태 중심으로 표시 |
| `frontend/components/drain-risk-list.tsx` | 연결 상태와 위험도 정렬/표시 보강 |
| `frontend/components/drain-summary-panel.tsx` | 선택 시설 패널은 최종 위험도, 수위, 유속, 막힘 정도 중심으로 유지 |
| `frontend/components/cctv-snapshot-card.tsx` | 이미지 없음/분석 실패/최근 이미지 없음 상태 보강 |
| `frontend/components/status/*` 또는 기존 컴포넌트 | 분석 중, 실패, 판단불가 상태 배지 보강 가능 |

## 7. 구현 단계

| 단계 | 작업 |
|---|---|
| 1 | 현재 백엔드 WebSocket endpoint와 `DRAIN_STATUS_UPDATED` payload 기준으로 프론트 타입 확정 |
| 2 | 기존 REST 초기 조회와 mock fallback이 깨지지 않도록 타입/adapter 보강 |
| 3 | WebSocket client 또는 hook 추가, 연결 상태와 reconnect 상태 관리 |
| 4 | 대시보드에서 `drainId` 기준으로 시설 목록/지도/선택 패널 부분 갱신 |
| 5 | 상세 화면은 별도 YOLO/XGBoost 결과 카드를 제거하고 MVP 첫 화면 기준의 현재 위험 상태로 정리 |
| 6 | 상세 화면에서 이벤트가 현재 시설에 해당할 때 `DRAIN_STATUS_UPDATED` 기준 최신 상태만 부분 갱신 |
| 7 | loading/error/empty/연결 끊김/이미지 없음 상태 점검 |
| 8 | `npm run lint`, `npm run build` 실행 후 결과 기록 |

## 8. 제외할 일

| 제외 항목 | 이유 |
|---|---|
| 새 지도 라이브러리 도입 | 현재 브랜치 목적은 실시간 갱신 안정화이며 Kakao 지도 구조 유지 |
| API 명세 전체 재작성 | 확정된 이벤트 흐름에 필요한 프론트 타입과 문서만 최소 반영 |
| 백엔드 WebSocket 구현 변경 | `/frontend` 밖 수정 금지 |
| DB/AI 서비스 구조 변경 | 프론트는 DB/AI에 직접 접근하지 않음 |
| WebSocket으로 이미지 파일 수신 | 확정 기준은 `imageUrl`만 전달 |
| 센서 이력 전체 WebSocket 수신 | 이력/차트는 REST API 조회 유지 |
| mock WebSocket 이벤트 구현 | 사용자는 백엔드 실제 데이터 기준 진행을 원함 |
| 상세 화면에 별도 YOLO/XGBoost 결과 카드 유지 | 1차 MVP에서는 현재 위험 상태 중심으로 충분하며 명시적 AI 원천 데이터 노출은 후순위 |

## 9. 추가 확인 필요 항목

아래 항목은 실제 구현 전 확인이 필요하다.

| 확인 항목 | 추천 방향 | 확인이 필요한 이유 |
|---|---|---|
| WebSocket URL 생성 방식 | `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`에서 `ws://localhost:8000/ws/drains/status`를 파생 | 새 환경변수 없이 MVP 구현 가능 |
| `drainId` 기준 | 현재 백엔드처럼 `drain_code` 문자열 사용 | REST `id`와 WebSocket `payload.drainId`를 같은 값으로 매칭 |
| 이벤트 타입명 | 현재 백엔드 기준 `DRAIN_STATUS_UPDATED` 사용 | 루트 명세와 백엔드 구현이 일치함 |
| 단계별 이벤트 필요 여부 | endpoint는 유지하고 내부 `type`만 추가하는 방식 추천 | 현재 백엔드에는 Sensor/YOLO/Failed broadcast가 없음 |
| 연결 실패 정책 | 자동 재연결은 적용하되 기존 REST 데이터 유지 | WebSocket이 끊겨도 화면이 비지 않게 하기 위함 |
| 상세 페이지 동기화 | 1차 구현은 REST 재조회 없이 `DRAIN_STATUS_UPDATED` payload 범위만 갱신 | YOLO 이미지 URL, YOLO 상태, confidence score 등 추가 데이터 확정은 후순위 |

## 10. 백엔드에 알려야 할 차이점

팀 흐름과 현재 백엔드 구현 사이의 차이는 다음과 같다. 이번 프론트 작업에서 직접 수정하지 않고, 필요 시 백엔드 담당자에게 전달한다.

| 차이점 | 현재 백엔드 | 팀 흐름 기준 | 영향 |
|---|---|---|---|
| WebSocket endpoint 개수 | `/ws/drains/status` 1개 | endpoint 1개 유지 | 프론트도 단일 socket client로 구현 |
| 이벤트 구분 방식 | 현재는 `type: DRAIN_STATUS_UPDATED`만 존재 | 같은 endpoint에서 `type`으로 구분 | parser를 `type` switch 구조로 작성 필요 |
| 센서 실시간 이벤트 | 없음 | 센서 수집 후 프론트에 전달 | 센서값만 먼저 갱신하는 1차 표시 불가 |
| YOLO 실시간 이벤트 | 없음 | YOLO 완료 즉시 프론트에 전달 | 최종 위험도 전 YOLO 중간 결과 표시 불가 |
| XGBoost 실시간 이벤트 | 있음, `DRAIN_STATUS_UPDATED` | 최종 위험도 전달 | MVP 최종 상태 갱신 가능 |
| 실패 이벤트 | 없음 | 분석 실패 시 오류 상태 전달 | YOLO/XGBoost 실패 영역별 표시 불가 |
| 이벤트 payload | 최종 상태 요약 필드 중심 | 단계별 상세 payload 가능성 | imageUrl, yoloStatus, confidenceScore 등은 WS로 받지 못함 |

프론트에서 “이상한 부분”으로 반드시 알려야 할 항목은 Sensor/YOLO/Failed 이벤트가 현재 백엔드에 없다는 점이다.

## 11. 남은 리스크

| 리스크 | 대응 |
|---|---|
| 팀 흐름의 단계별 실시간 반영과 현재 백엔드 구현이 다름 | MVP는 `DRAIN_STATUS_UPDATED`로 먼저 연결하고, 단계별 이벤트는 백엔드 후속 작업으로 분리 |
| 이벤트 payload에 YOLO 상세 필드가 없음 | 1차 구현에서는 YOLO/XGBoost 원천 데이터 노출을 제외하고 막힘률/최종 판단 중심으로 표시 |
| 이벤트 payload에 sensor measuredAt이 없음 | `updatedAt`을 최신 표시 시각으로 사용하거나 REST 재조회 여부 확인 |
| WebSocket 연결 실패 시 화면 혼란 | 연결 상태 chip과 기존 REST 데이터 유지 정책 적용 |
| 상세 화면 문자열/표시 품질 이슈 | 실시간 작업 중 깨진 문구가 발견되면 `/frontend` 안에서 별도 보정 가능 여부 확인 |

## 12. 추천 진행 방향

MVP 안정화를 기준으로 추천하는 방향은 다음과 같다.

| 우선순위 | 방향 |
|---|---|
| 1 | 현재 백엔드 구현과 루트 명세에 맞춰 `DRAIN_STATUS_UPDATED` 수신 기능을 먼저 구현 |
| 2 | WebSocket URL은 `NEXT_PUBLIC_API_BASE_URL`에서 파생하고, 필요 시에만 `NEXT_PUBLIC_WS_URL`을 추가 |
| 3 | socket client는 단일 endpoint에 연결하고, 메시지 내부 `type`으로 handler를 분기 |
| 4 | 이벤트 수신 시 `payload.drainId`와 REST `id`를 매칭해 대시보드 항목만 부분 갱신 |
| 5 | 연결이 끊겨도 기존 REST 데이터는 유지하고 연결 상태만 표시 |
| 6 | 상세 화면은 MVP 첫 화면 레퍼런스 기준으로 정리하고, 별도 YOLO/XGBoost 결과 카드는 제거 |
| 7 | Sensor/YOLO/Failed 단계별 이벤트와 필요 데이터 확정은 후순위로 둠 |
| 8 | 단계별 이벤트가 필요하다는 결정이 나면 endpoint 추가가 아니라 같은 endpoint의 `type` 확장으로 요청 |

## 13. 구현 가능성 체크

현재 코드 기준으로 프론트 구현은 가능하다. 단, 구현 가능한 범위와 백엔드 추가가 필요한 범위를 구분해야 한다.

| 항목 | 가능 여부 | 근거 | 비고 |
|---|---|---|---|
| WebSocket endpoint 연결 | 가능 | `backend/app/main.py`에서 `websocket.router`를 include하고, `backend/app/routers/websocket.py`에 `/ws/drains/status`가 있음 | 프론트에서 `ws://localhost:8000/ws/drains/status`로 연결 가능 |
| 단일 endpoint 유지 | 가능 | 백엔드 endpoint가 이미 1개이고, 메시지에 `type` 필드가 있음 | 프론트 parser를 `type` switch 구조로 작성 |
| `DRAIN_STATUS_UPDATED` 수신 | 가능 | `backend/app/schemas/api_response.py`의 `drain_status_event_payload`가 해당 payload 생성 | 현재 MVP에서 우선 구현할 수 있는 이벤트 |
| XGBoost 결과 후 실시간 갱신 | 가능 | `backend/app/routers/analysis.py`에서 XGBoost 생성 후 `manager.broadcast(...)` 실행 | 지도, 목록, 상세 상태 갱신 가능 |
| REST `id`와 WS `drainId` 매칭 | 가능 | 백엔드 payload는 `drain.drain_code`를 `drainId`로 내려줌 | 프론트 REST `id`와 같은 외부 식별자로 맞추면 됨 |
| WebSocket URL 파생 | 가능 | 프론트 `.env.example`에 `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` 존재 | `http`→`ws`, `https`→`wss` 변환으로 처리 |
| 연결 상태 표시 | 가능 | `DrainRiskList`에 `waiting/connected/reconnecting/error` UI가 이미 있음 | 실제 socket 상태와 연결하면 됨 |
| 센서 단독 실시간 갱신 | 현재 불가 | `POST /api/sensor-data`에는 broadcast가 없음 | 백엔드에서 같은 endpoint로 `SENSOR_DATA_UPDATED` 발행 필요 |
| YOLO 중간 결과 실시간 갱신 | 현재 불가 | `POST /api/analysis/yolo`에는 broadcast가 없음 | 백엔드에서 같은 endpoint로 `YOLO_RESULT_UPDATED` 발행 필요 |
| 분석 실패 이벤트 표시 | 현재 불가 | 실패 시 broadcast 이벤트가 없음 | 백엔드에서 `ANALYSIS_FAILED` 발행 필요 |
| YOLO 이미지 URL 실시간 반영 | 현재 제한적 | `DRAIN_STATUS_UPDATED` payload에 `imageUrl`, `yoloStatus`, `confidenceScore`가 없음 | 필요하면 이벤트 수신 후 최신 분석 REST 재조회 또는 payload 확장 필요 |

결론적으로 이번 프론트 구현은 `DRAIN_STATUS_UPDATED` 기준의 최종 상태 실시간 반영까지 가능하다. 팀에서 말한 센서, YOLO, 실패 단계별 반영은 같은 WebSocket endpoint에서 내부 `type`을 확장하면 구조적으로 가능하지만, 현재 백엔드가 해당 이벤트를 발행하지 않으므로 프론트 단독으로는 완성할 수 없다.

## 14. 상세 화면 레퍼런스 기준 데이터 확인

`docs/legacy-mvp/image/02_detail_layout_reference.png` 기준으로 상세 화면을 맞출 때 필요한 데이터는 대부분 현재 상세 REST API와 이력 API에 포함되어 있다. 따라서 화면 구성을 맞추기 위해 무조건 새 API를 요청할 상황은 아니다.

루트 문서 확인 결과 `docs/legacy-mvp/01_프로젝트정의서.md`, `docs/legacy-mvp/03_요구사항정의서.md`, `docs/legacy-mvp/04_MVP범위.md`, `docs/legacy-mvp/05_와이어프레임.md`, `docs/legacy-mvp/10_역할분담_일정_발표목차.md`에는 상세 화면에서 YOLO 분석 결과와 XGBoost 판단 결과를 확인해야 한다는 내용이 있다. 다만 1차 MVP 화면에서는 이를 원천 데이터 카드로 직접 노출하지 않고, 최종 표시값에 녹여서 보여준다.

즉, 1차 구현에서는 `yoloStatus`, `confidenceScore`, `yoloResultId`, `xgboostId` 같은 세부 분석 데이터는 화면에 직접 표시하지 않는다. 레퍼런스 첫 화면 기준으로는 `막힘 정도`, `상태`, `위험 점수`, `최종 판단`, `최근 업데이트`처럼 관리자 판단에 필요한 값만 표시하는 방향이 적절하다.

| 화면 영역 | 레퍼런스 표시 내용 | 현재 데이터 충족 여부 | 확인/요청 필요 |
|---|---|---|---|
| 상단 제목 | 시설 ID, 주소 또는 도로명 | 충족 | `GET /api/drains/{id}`의 `id`, `roadAddress`, `fullAddress` 사용 |
| CCTV 영역 | 최근 스냅샷 1장, 썸네일 여러 장, 최근 캡처 시각 | 부분 충족 | 현재는 최신 `imageUrl` 1장 중심. 여러 썸네일이 필수면 이미지 목록 API 또는 YOLO 결과 목록 활용 필요 |
| 위치 지도 | 단일 시설 위치 마커, 주소 | 충족 | `latitude`, `longitude`, `fullAddress` 사용. 지도 타일은 프론트/Kakao SDK 영역 |
| 센서 차트 | 수위/유속 추세, 24시간/7일 토글 | 부분 충족 | `sensorHistory`와 `/sensors` API 사용 가능. 다만 `range=24h/7d`가 실제 필터링되는지 백엔드 확인 필요 |
| 센서 KPI | 현재 수위/유속, 최고 수위/유속, 최고 시각 | 부분 충족 | 현재/최고값은 프론트가 `sensorHistory`에서 계산 가능. 정확한 기간 기준은 백엔드 range 지원 여부에 의존 |
| 현재 위험 상태 | 상태, 막힘 정도, 수위, 유속, 최근 업데이트, 판정 결과 | 충족 | `riskLevel`, `obstructionRatio`, `waterLevelCm`, `flowVelocityMps`, `updatedAt`, `finalDecision` 사용 |
| 시설 정보 | 시설 ID, 주소, 상태, 막힘 정도, 수위, 유속, 최근 업데이트 | 충족 | 상세 DTO와 adapter로 표시 가능 |
| 과거 위험 이력 | 최근 7일 위험도, 점수, 시각 | 충족 | `riskHistory` 또는 `/risk-history?days=7` 사용 |
| YOLO 분석 결과 | 막힘 상태, 막힘 비율, 신뢰도, 분석 시각 | 1차 제외 | 명시적 YOLO 원천 데이터는 표시하지 않고 `obstructionRatio` 기반 막힘 정도만 표시 |
| XGBoost 결과 | 위험 점수, 위험도, 최종 판단 | 부분 표시 | `riskScore`, `riskLevel`, `finalDecision`처럼 현재 상태에 필요한 최종 표시값만 사용 |
| 알림/사용자 아이콘 | 알림 수, 사용자 메뉴 | 상세 데이터와 무관 | 앱 공통 header UI 영역. 백엔드 상세 API 요청 대상 아님 |

추가로 백엔드 담당자에게 확인하면 좋은 데이터 기준은 아래 정도다.

| 확인 항목 | 이유 |
|---|---|
| `GET /api/drains/{id}/sensors?range=24h/7d`가 실제 기간 필터링을 하는지 | 레퍼런스의 24시간/7일 토글을 정확히 구현하려면 필요 |
| 스냅샷 썸네일 여러 장이 MVP 필수인지 | 현재 상세 응답은 최신 이미지 1장 중심이라 썸네일 여러 장은 별도 데이터가 필요할 수 있음 |
| 유속 단위 표시를 `m/s`로 통일할지, 레퍼런스처럼 `m³/min`으로 표시할지 | 현재 백엔드 필드는 `flowVelocityMps`라서 단위는 `m/s`가 자연스러움 |
| WebSocket 최종 이벤트 후 상세 화면에서 최신 분석 REST를 재조회할지 | 1차 구현에서는 재조회하지 않고, 필요 데이터 확정 후 후순위로 검토 |

정리하면 1차 구현은 상세 화면을 MVP 첫 화면 기준으로 정리하고, 명시적인 YOLO/XGBoost 원천 데이터 카드는 제거한다. 대신 현재 WebSocket과 REST가 제공하는 `obstructionRatio`, `riskScore`, `riskLevel`, `finalDecision` 같은 최종 표시값만 사용한다. 레퍼런스 이미지에 맞추기 위해 더 확인할 것은 `센서 range 필터링`, `스냅샷 여러 장 필요 여부`, `유속 단위`, `실시간 이벤트 후 상세 최신 분석 재조회 여부`지만, 이 항목들은 WebSocket 연결과 1차 안정화 이후 후순위로 둔다. 그 외 시설 정보, 위험 상태, 지도, 위험 이력은 현재 API로 구현 가능하다.

## 15. 사용자 승인 후 진행 기준

사용자 승인 후 다음 순서로 구현한다.

1. 현재 백엔드의 `/ws/drains/status`와 `DRAIN_STATUS_UPDATED` 기준으로 구현한다.
2. mock WebSocket 이벤트는 구현하지 않는다.
3. 상세 화면은 MVP 첫 화면 기준으로 정리하고, 명시적인 YOLO/XGBoost 원천 데이터 카드는 제거한다.
4. 필요 데이터 확정 영역은 후순위로 두고, 1차는 WebSocket 연결과 최종 상태 갱신을 우선한다.
5. `/frontend` 내부에서만 타입, adapter, hook/client, 화면 상태를 수정한다.
6. Sensor/YOLO/Failed 이벤트 부재는 백엔드 확인 필요 항목으로 보고한다.
7. `npm run lint`, `npm run build` 결과를 작업 완료 문서와 최종 보고에 남긴다.

## 16. 추천 커밋 메시지

제목:

```text
docs: MVP 기준 실시간 대시보드 안정화 계획 정리
```

내용:

```text
- 백엔드 WebSocket 구현과 루트 API 명세를 확인해 MVP 실시간 갱신 계획을 갱신한다.
- /ws/drains/status와 DRAIN_STATUS_UPDATED 기준의 프론트 구현 방향을 정리한다.
- 단일 WebSocket endpoint에서 메시지 type으로 이벤트를 구분하는 방향을 반영한다.
- 현재 백엔드 기준 구현 가능 범위와 추가 백엔드 이벤트가 필요한 범위를 구분한다.
- 상세 화면 레퍼런스 기준으로 추가 확인이 필요한 데이터 항목을 정리한다.
- 1차 MVP에서는 명시적인 YOLO/XGBoost 원천 데이터 카드를 제외하고 최종 표시값 중심으로 상세 화면을 정리한다.
- 필요 데이터 확정은 후순위로 두고 WebSocket 연결과 최종 상태 갱신을 1차 범위로 둔다.
- Sensor, YOLO, Failed 단계별 이벤트 부재를 백엔드 확인 필요 항목으로 기록한다.
```

