# 09 10개 빗물받이 실시간 대시보드 안정화 및 UI 개선 로드맵

## 1. 작업 개요

| 항목 | 내용 |
| --- | --- |
| 현재 브랜치 | `feature/realtime-drain-store-hardening` |
| 현재 작업 범위 | `/frontend` 내부 실시간 상태 정합성, 연결 복구, 오류 UI 안정화 계획 및 후속 구현 |
| 대상 규모 | 서로 다른 시나리오를 수신하는 빗물받이 10개 |
| 기준 계약 | `docs/contract/backend-contract-doc.md` 및 현재 Backend-AI 통합 이벤트 |
| 목표 | 이벤트 유실, 늦은 이벤트, REST/WS 경합에도 지도·목록·상세·차트가 일관된 최신 데이터를 표시하게 한다. |

이번 문서는 단순 WebSocket 재연결이 아니라 10개 시설이 각기 다른 분석 결과를 받는 데모/운영 조건에서 필요한 **상태 정합성, 화면 복구력, 관측 가능한 UI**를 단계별로 정리한다. 기존 UI 디자인은 유지하고, 데이터 흐름을 우선 안정화한다.

## 2. 확인한 기준과 현재 상태

| 기준/파일 | 확인 결과 |
| --- | --- |
| `AGENTS.md` | 중간 이상 작업은 plan 작성 후 사용자 승인, 상태 관리 방식/폴더 구조/API 연동 변경은 사전 확인이 필요하다. |
| `docs/convention/documentation-convention.md` | plan에는 작업 범위, 변경 내용, 사용자 확인 항목, 추천 방향을 기록한다. |
| 루트 `docs/legacy-mvp/08_기술스택선정근거.md` | 목표 아키텍처는 TanStack Query(서버 상태)와 Zustand(전역/WS 상태)를 사용한다고 정의한다. |
| `frontend/package.json` | 계획 작성 시 TanStack Query와 Zustand가 없었고, 사용자 승인 후 이번 브랜치에서 Zustand를 설치한다. TanStack Query는 후속 판단으로 둔다. |
| `docs/contract/backend-contract-doc.md` | 단일 WS endpoint에서 `DRAIN_STATUS_UPDATED`, `YOLO_RESULT_UPDATED`, `XGBOOST_RESULT_UPDATED` 세 이벤트를 사용한다. |
| `lib/websocket/drain-status-socket.ts` | cleanup과 3초 재연결은 있으나 재연결 후 REST 재동기화, backoff, 단일 상태원은 없다. |
| `app/page.tsx`, `app/drains/[id]/page.tsx` | 대시보드와 상세가 각자 로컬 상태와 WS 구독을 가진다. 대시보드 내부 UI는 같은 상태를 공유하지만 상세는 별도 상태다. |
| `lib/api/adapters.ts` | `drainId` 기준 부분 병합은 있으나 `updatedAt` 비교가 없어 과거 이벤트가 최신 상태를 덮을 수 있다. |
| PR 13 통합 테스트 결과 | AI 분석 1회에 YOLO → XGBoost → 최종 상태 이벤트가 수신되는 계약과 REST 이력 조회가 확인되어 있다. |

### 2.1 유지할 이벤트 계약

현재 프로젝트에서 이벤트명 변경이나 새 이벤트 강제는 하지 않는다.

| 이벤트 | 현재 역할 | 프론트 반영 영역 |
| --- | --- | --- |
| `DRAIN_STATUS_UPDATED` | 최종 위험 상태와 센서/막힘 요약 | 지도, 위험 목록, 요약, 선택 시설 패널 |
| `YOLO_RESULT_UPDATED` | CCTV 이미지와 YOLO 분석 결과 | 상세 CCTV, YOLO 탭, 이미지 이력 |
| `XGBOOST_RESULT_UPDATED` | 최종 위험 판단과 참조 결과 ID | 상세 위험 요약, XGBoost 탭, 위험 이력 |

`eventId`, `analysisId`, top-level `timestamp`는 현재 계약에 추가하지 않는다. 결과 ID와 각 이벤트의 기존 시간 필드가 현재 UI 목적에는 충분하다.

- 중복 방지: `yoloResultId`, `xgboostResultId`
- 최종 상태 최신성: `DRAIN_STATUS_UPDATED.payload.updatedAt`
- YOLO 최신 결과: `analyzedAt` (fallback `updatedAt`)
- XGBoost 최신 결과: `evaluatedAt` (fallback `updatedAt`)

향후 프론트가 분석 요청을 직접 시작하고 진행/실패 상태를 추적하게 되면, 그때 `requestId`를 pending/failed 상태 상관관계 키로 추가 요청한다.

## 3. 10개 시나리오에서 우선 해결할 위험

| 우선순위 | 위험 | 현재 문제 | 대응 방향 |
| ---: | --- | --- | --- |
| P0 | 재연결 중 이벤트 유실 | WS 재연결 후 누락 구간을 복구하지 않는다. | 재연결 성공 후 기존 REST 목록/요약을 재조회하고, 시간 비교 merge로 반영한다. |
| P0 | 늦은 이벤트 역전 | 이전 `updatedAt` 이벤트가 최신 화면을 되돌릴 수 있다. | 이벤트 종류별 최신성 비교와 결과 ID 중복 제거를 공통 handler에 둔다. |
| P0 | REST와 WS 경합 | REST 응답이 요청 중 받은 더 최신 WS 데이터를 덮을 수 있다. | REST 결과도 store의 시설별 최신 시각보다 새 경우에만 merge한다. |
| P1 | 화면별 데이터 불일치 | 대시보드와 상세가 다른 로컬 상태를 유지한다. | 공유 drain 상태 source를 만들고 페이지는 selector로 읽는다. |
| P1 | API 장애가 mock처럼 보임 | API 실패가 mock fallback으로 전환돼 운영 장애를 가린다. | `api` / `mock` / `error`를 분리하고 실제 오류를 명확히 표시한다. |
| P1 | 관측 부족 | 연결 끊김, stale 데이터, 재동기화 실패를 사용자가 알기 어렵다. | 연결 배지와 마지막 정상 동기화 시각, 재시도 행동을 제공한다. |
| P2 | 10개 동시 갱신 렌더 비용 | 배열 전체 map/정렬로 관련 없는 UI도 갱신될 수 있다. | `drainsById`와 selector 기반 구독으로 필요한 단위만 갱신한다. 과도한 memo는 피한다. |

## 4. 이번 브랜치 구현 목표

### 4.1 기술 선택 비교와 권장 결정

10개 시설의 동시 시나리오에서 가장 중요한 것은 단순 성능이 아니라 **REST와 WS가 같은 최신 상태를 갱신하는 단일 source**다. 도구를 한 번에 여럿 도입하면 이 source가 오히려 둘 이상이 될 수 있으므로, 각 역할을 분리한다.

| 영역 | 후보 | 이번 브랜치 결정 | 이유 | 후속 도입/재검토 조건 |
| --- | --- | --- | --- | --- |
| 실시간/전역 상태 | Context + `useReducer` | 대안 | 의존성 없이 구현 가능하지만 Context value 변경 시 selector 기반 렌더 제어가 번거롭다. | 새 패키지를 원하지 않거나 Zustand 승인 전일 때 |
| 실시간/전역 상태 | **Zustand** | **권장 도입** | 루트 기술스택의 의도와 맞고, drain별 selector·액션·연결 상태를 작게 분리해 지도/목록/상세의 불필요한 렌더를 줄이기 쉽다. | 패키지 설치와 상태 관리 방식 변경 승인 필요 |
| 서버 상태 | Axios 직접 호출 + Zustand merge | **이번 사용** | REST 초기/재연결 응답을 realtime store의 최신성 규칙으로 단일하게 병합할 수 있다. | 현재 6개 내외 API와 10개 시설에는 충분 |
| 서버 상태 | TanStack Query | 보류 | 캐시·refetch·loading/error에는 강하지만, 도입 직후 Query cache와 realtime store가 이중 source가 될 위험이 있다. | REST 화면·캐시 정책이 늘고 Query cache를 유일한 서버 source로 설계할 때 |
| WebSocket | 직접 client | **이번 사용** | 기존 socket 코드와 계약이 단순하며, 핵심인 event merge 규칙을 직접 통제할 수 있다. | heartbeat/shared socket/send queue가 복잡해질 때 `react-use-websocket` 검토 |
| payload 검증 | 수동 type guard | **이번 사용** | 현재 3개 이벤트의 필수 필드를 가볍게 검증할 수 있다. | 외부 이벤트 버전이 늘거나 계약 변동이 잦으면 Zod 검토 |
| mock | 명시적 mock mode | **이번 사용** | 실제 API 오류를 데모 mock으로 숨기지 않는다. | 독립 프론트 테스트가 커지면 MSW 검토 |
| E2E | 수동 시나리오 점검 | **이번 사용** | 이번 브랜치의 정합성 규칙을 빠르게 검증한다. | 반복 회귀가 필요하면 Playwright 도입 |
| 시간 처리 | `Date.parse()` + 공통 helper | **이번 사용** | ISO-8601 최신성 비교에는 충분하다. | 복잡한 시간대/표시 포맷 요구가 늘면 date-fns 검토 |

**권장 조합:** 이번 브랜치에서 Zustand를 도입하고, REST 호출은 기존 Axios API 계층을 유지한다. TanStack Query는 이번에 함께 넣지 않는다. 이는 “좋은 도구를 덜 쓰자”가 아니라, realtime store를 먼저 하나로 안정화한 다음 Query cache의 책임을 안전하게 설계하기 위한 순서다.

TanStack Query는 다음 중 하나가 성립할 때 별도 브랜치에서 도입한다.

1. 대시보드 외에 시설 검색, 필터, 대응 이력, 작업자 화면 등 REST 중심 화면이 늘어난다.
2. 화면 간 캐시 공유, background refetch, 요청 취소/중복 제거 요구가 커진다.
3. Query cache를 서버 데이터의 유일한 source로 정하고, WS 이벤트는 `queryClient.setQueryData`로 patch하는 설계를 팀이 합의한다.

이번 Zustand store는 클라이언트 UI 상태와 실시간으로 병합된 facility view model을 보유한다. TanStack Query를 추후 도입하더라도 같은 drain 데이터를 Query cache와 Zustand에 무비판적으로 복제하지 않는다.

### 4.2 권장 구조

Zustand store를 공통 source로 두고, 컴포넌트는 필요한 selector만 구독한다. 이는 10개 시설에서 특정 drain 이벤트가 들어올 때 다른 시설 상세/마커가 불필요하게 갱신되는 것을 줄이는 데 알맞다.

```text
REST 초기 조회 · 재연결 동기화
             │
             ▼
useDrainStore (Zustand)
  - drainsById, selectedDrainId
  - connectionStatus, lastSyncedAt
  - 이벤트/REST 최신성 검증 및 merge
             ▲
             │
websocket-client + event-handlers
             │
             ▼
Dashboard: 지도 · 목록 · 요약 · 선택 패널
Detail: drainId로 같은 시설 상태 조회 + 이력 표시
```

권장 파일 방향:

| 위치 | 책임 |
| --- | --- |
| `lib/realtime/realtime-types.ts` | 현재 3개 WS 이벤트 union, 시간/결과 ID 접근 helper 타입 |
| `lib/realtime/event-handlers.ts` | 이벤트 검증, 중복 제거, 이벤트 종류별 최신성 판단, partial patch 생성 |
| `lib/realtime/websocket-client.ts` | 단일 연결 lifecycle, cleanup, bounded reconnect, 재연결 성공 알림 |
| `lib/api/drains.ts` | 기존 목록/요약/상세 호출을 재동기화 용도로 재사용 |
| `store/drain-store.ts` | Zustand 공통 상태, drain별 selector, REST/WS merge action |
| `components/dashboard/*` | 기존 화면의 표시 컴포넌트 분리. UI 형태와 색상은 유지 |

기존 `lib/websocket/drain-status-socket.ts`는 호환 wrapper로 유지하거나, 모든 호출부 이전이 끝난 후 제거 여부를 결정한다. 한 번에 불필요한 대규모 UI 재작성은 하지 않는다.

권장 store 책임:

```text
drainsById
selectedDrainId
connectionStatus / reconnectCount / lastSyncedAt
mergeRestDrains()
applyDrainStatusEvent()
applyYoloEvent()
applyXgboostEvent()
```

### 4.3 최신성 및 병합 규칙

1. 모든 시간값은 ISO-8601 파싱 성공 시에만 비교한다. 파싱 실패 이벤트는 화면 상태를 변경하지 않고 개발 환경에서만 진단 가능하게 둔다.
2. `DRAIN_STATUS_UPDATED`는 같은 `drainId`의 현재 `updatedAt`보다 **엄격히 최신일 때만** 최종 상태를 patch한다.
3. `YOLO_RESULT_UPDATED`는 `yoloResultId`로 dedupe한다. 이력은 늦게 도착해도 보존하고 `analyzedAt` 내림차순으로 정렬한다. 최신 CCTV/막힘률만 시간상 더 최신인 결과로 갱신한다.
4. `XGBOOST_RESULT_UPDATED`도 `xgboostResultId`로 dedupe한다. 위험 이력은 보존·정렬하고, 현재 위험 상태는 `evaluatedAt`이 더 최신인 경우만 갱신한다.
5. 재연결 뒤 REST 재조회 결과는 전체 replace하지 않는다. `drainId`별 시간 비교 merge를 적용해 WS로 먼저 도착한 새 값을 보존한다.
6. 시간값이 같은 경우 결과 ID가 더 큰 값을 우선하지 않는다. ID의 증가 순서를 시간 순서로 가정하지 않으며, 동일 시각은 현재 값을 유지해 화면 흔들림을 피한다.

### 4.4 연결 복구와 UI

- 최초 REST 조회 성공 뒤에만 WS를 연결한다.
- close 후 3초 고정 재시도 대신 최대 대기 시간이 있는 exponential backoff를 적용한다. 10개 시설 MVP에서는 무한 폭주 방지와 사용자 상태 표시를 우선한다.
- 재연결이 열린 직후 대시보드는 `getDrains()`와 `getDashboardSummary()`를 재조회한다. 별도 `status/latest` API는 현재 필요하지 않다.
- 상세 화면은 해당 drain의 detail/latest/history를 필요 범위로 재조회한다. 이력 API 실패는 최신 상태 표시를 막지 않는다.
- UI에는 `connecting`, `connected`, `reconnecting`, `disconnected`, `error`를 구분한다. `lastSyncedAt` 기준 stale 안내와 수동 재시도 버튼을 제공한다.
- API 요청 실패와 의도적 mock mode를 분리한다. mock은 개발/데모에서만 명시적으로 선택하며, 실제 API 오류는 오류 UI로 보여준다.

### 4.5 이번 브랜치 완료 기준

1. 동일 페이지 렌더링으로 WS가 중복 생성되지 않고 unmount 시 reconnect timer와 socket이 정리된다.
2. WS 재연결 성공 뒤 REST 재동기화가 실행되며, REST/WS 경합에도 최신 값이 유지된다.
3. 10개 시설 중 한 시설 이벤트가 다른 9개 시설의 표시값을 바꾸지 않는다.
4. 늦은 `DRAIN_STATUS_UPDATED`는 현재 상태를 되돌리지 않는다.
5. 늦은 YOLO/XGBoost 이벤트는 이력에는 남지만 최신 요약을 되돌리지 않는다.
6. 지도·목록·요약·선택 패널·상세가 공통 source의 같은 시설 상태를 읽는다.
7. 연결/재연결/오류/stale/empty/image fallback 상태를 사용자가 구분할 수 있다.
8. `pnpm lint`, `pnpm build`와 10개 시나리오 수동 점검을 통과한다.

## 5. 10개 시설 시나리오 검증 계획

각 시설에 고정된 역할을 두지 않고, 아래 상태 조합을 10개 drain에 분배해 반복 가능하게 검증한다.

| 검증 | 기대 결과 |
| --- | --- |
| 서로 다른 drainId의 동시 3종 이벤트 | 해당 시설의 지도 마커, 목록, 상세만 갱신된다. |
| 같은 drain의 YOLO → XGBoost → 상태 이벤트 | 이력과 최신 요약이 이벤트 책임에 맞게 갱신된다. |
| 과거 상태 이벤트를 최신 이벤트 뒤에 전송 | 최신 위험도/수위/막힘률이 유지된다. |
| 중복 YOLO/XGBoost 이벤트 전송 | 이력 항목이 중복되지 않는다. |
| WS 중단 후 여러 drain 상태 변경 | 재연결 및 REST 동기화 뒤 10개 상태가 서버 값과 일치한다. |
| REST 응답 지연 중 WS 새 이벤트 수신 | 늦은 REST 응답이 WS 최신 값을 덮지 않는다. |
| 이미지 URL 실패 | CCTV 영역만 placeholder로 대체되고 다른 정보는 유지된다. |
| 분석 이력 없음 | 빈 이력/분석 대기 UI가 표시되고 화면은 유지된다. |
| API 오류 | mock 데이터로 위장하지 않고 재시도 가능한 오류 상태를 보인다. |
| 10개 순차·동시 이벤트 | 마커 깜빡임이나 선택 시설 변경 없이 화면이 반영된다. |

## 6. 후속 브랜치 제안

시나리오는 AI 모델과 백엔드 데이터 생성 방식이 확정된 뒤 설계한다. 따라서 지금은 특정 시설별 위험 시나리오나 데모 제어를 구현 목표로 고정하지 않는다.

### 6.1 프론트엔드 단독으로 진행 가능한 후속 작업

| 순서 | 추천 브랜치 | 목표 | 선행 조건 |
| ---: | --- | --- | --- |
| 1 | `feature/realtime-drain-store-hardening` | 이번 문서의 상태 정합성, 재연결 복구, 오류 UI 기반 구현 | 아래 사용자 확인 |
| 2 | `refactor/dashboard-realtime-components` | `components/dashboard/*`로 표시 컴포넌트 분리, Zustand selector 사용, UI 회귀 최소화 | 1단계 공통 source 안정화 |
| 3 | `feat/tanstack-query-server-state` | TanStack Query를 REST 서버 상태의 단일 cache로 도입하고 WS patch 경계를 정의 | REST 중심 화면 증가 및 cache/source 설계 합의 |
| 4 | `test/realtime-dashboard-e2e` | 배포 후 실제 화면 변경을 반복 검증할 수 있는 E2E 기반을 마련한다. 시나리오 데이터는 백엔드가 제공하는 실제 데이터만 사용한다. | 화면 흐름 안정화, Playwright 설치 승인, 배포 환경 접근 방법 합의 |
| 5 | `feat/analysis-progress-observability` | 분석 요청-진행-실패 UI와 요청 상관관계 표시 | 백엔드가 `requestId`와 processing/failed 계약을 제공 |

### 6.2 팀 협의가 필요한 후속 작업

| 후보 | 프론트에서 미리 할 수 있는 일 | 팀/백엔드와 확정할 내용 | 현재 결정 |
| --- | --- | --- | --- |
| AI 기반 시나리오 | 화면의 loading, unknown, 오류 placeholder를 유지 | 모델 출력 범위, 10개 시설별 입력 데이터, 이벤트 순서와 재현 방법 | 모델 확정 후 설계 |
| 데모 제어 API | 제어 패널 UI 초안만 검토 가능 | start/stop/reset/scenario endpoint, 초기화 범위, 동시 실행 방지, 권한 | 구현 약속 없음. 필요 시 별도 브랜치 |
| TanStack Query | 도입 경계와 cache invalidation/WS patch 초안 작성 | 서버 상태 source를 Query cache로 둘지 Zustand로 둘지 팀 합의 | 다음 리팩토링에서 재검토 |
| 실제 이미지 URL | 현재 fallback placeholder를 정상 UX로 유지 | AI/백엔드가 브라우저 접근 가능한 이미지 URL, 보존 기간, CORS를 제공 | 백엔드 계약 후 반영 |
| 분석 진행/실패 | pending/failed UI 공간과 상태 문구 준비 | `requestId`, processing/failed event 또는 job status API | 계약 확정 후 구현 |
| 배포 후 E2E | 브라우저 검증 항목을 문서화 | 테스트 대상 배포 URL, seed/reset 방식, 테스트 계정/데이터 정책 | 필요 시 Playwright 도입 |

## 7. 사용자 확인 필요 항목

코드 수정 전 다음 결정을 확인한다.

1. **상태 관리 방식**: 승인됨. 이번 브랜치에서 Zustand를 설치하고, `drainsById`·선택 시설·WS 연결 상태·REST/WS merge action의 공통 source로 사용한다.
2. **재동기화 API**: 신규 `/status/latest` API를 만들지 않고, 현재 `GET /api/drains`와 `GET /api/dashboard/summary`로 재연결 복구를 구현한다.
3. **mock 정책**: 승인됨. 자동 mock fallback을 제거한다. 실제 API 오류는 실패 상태와 기존 placeholder 이미지로 표현하며, 시나리오 데이터도 향후 백엔드가 제공한다.
4. **UI 범위**: 승인됨. 기존 레이아웃과 디자인을 유지하고, 현재 UI를 과도하게 바꾸지 않는 범위에서 연결 상태 배지, stale 안내, 재시도 버튼, 빈 분석/이력 상태를 더한다.
5. **TanStack Query 도입 시점**: 루트 문서의 목표 스택임은 유지하되 이번 브랜치에는 설치하지 않는다. Zustand store와 Query cache의 이중 source 방지 설계를 별도 브랜치에서 확정한 뒤 도입한다.
6. **컴포넌트 이동 범위**: 승인됨. 이번 브랜치는 데이터 계층 중심으로 하고, v0 유래 컴포넌트 분리/리팩토링은 다음 프론트엔드 단독 브랜치에서 다룬다.
7. **데모 제어 API**: 팀 회의가 필요한 항목이다. 후속 협의 후보로만 남기고 구현을 약속하지 않는다.
8. **테스트 도구**: 현재는 도입하지 않는다. 배포 후 화면 변경을 반복 검증할 필요가 생기면 실제 백엔드 데이터를 대상으로 하는 E2E 도입을 팀과 협의한다.

## 8. 범위 밖 항목과 백엔드 확인 사항

| 항목 | 이번 브랜치 처리 | 후속/확인 |
| --- | --- | --- |
| 이벤트명 변경 | 하지 않음 | 현재 계약 유지 |
| `eventId`, `analysisId`, top-level timestamp 추가 | 하지 않음 | 분석 진행/실패 UI가 필요해질 때 `requestId` 계약 검토 |
| 실제 이미지 제공 | fallback 유지 | `ai-server://mock/*`을 브라우저 접근 가능한 URL로 바꾸는 백엔드/AI 과제 |
| WS heartbeat | 프론트 reconnect 동작은 보강 | 프록시/장기 연결 환경 확정 후 ping/pong 또는 서버 keepalive 검토 |
| 데모 제어 | UI 미구현 | 팀 회의에서 필요성이 확정될 때만 API endpoint, reset 범위, 동시 실행 방지, 권한을 협의 |
| 분석 실패 상태 | 현재 계약만으로 임의 추정하지 않음 | failed event 또는 REST job status 제공 여부 확인 |

## 9. 완료 후 기록 및 검증

- 구현 결과: `docs/steps/step-11-realtime-dashboard-stability-result.md`
- PR 요약: `docs/pr/pr-14-realtime-dashboard-stability.md`
- 검증: `pnpm lint`, `pnpm build`, 10개 시나리오 수동 체크리스트
- 기록할 항목: 재연결 전후 서버 상태 비교, 과거 이벤트 무시 결과, REST/WS 경합 결과, UI 상태 스크린샷, 남은 백엔드 의존성

## 10. 추천 커밋 메시지

제목:

```text
docs: 10개 시설 실시간 대시보드 안정화 로드맵 추가
```

내용:

```text
- 10개 빗물받이 시나리오 기준 실시간 상태 정합성 위험을 정리한다.
- 재연결 REST 동기화와 이벤트별 최신성 병합 규칙을 정의한다.
- 이번 브랜치와 후속 UI, 데모, E2E 작업의 승인 항목을 문서화한다.
```

