# 06 실시간 분석 계약 반영 상세 화면 개선 계획

## 1. 작업 개요

| 항목 | 내용 |
|---|---|
| 브랜치 | `feature/realtime-analysis-websocket-contract-modify` |
| 작업 범위 | `/frontend` 내부 코드 및 문서 |
| 기준 계약 | `docs/contract/backend-contract-doc.md`, 첨부 백엔드 전달안 |
| 목적 | 추가 WebSocket/REST 계약에 맞춰 상세 화면에서 최신 YOLO 이미지, 막힘 정도, 수위, XGBoost 판단 근거를 안정적으로 표시한다. |

이번 작업은 상세 화면 정보 구조와 API 데이터 계층을 함께 바꾸는 중간 규모 작업이다. 코드 수정 전 사용자 확인이 필요한 이미지 이력 UI 방향을 먼저 확정한 뒤 진행한다.

## 2. 확인한 기준

- `AGENTS.md`: `/frontend` 내부 작업, 실제 구조 확인, 중간 이상 작업 plan 작성, 코드 수정 전 사용자 승인 기준을 확인했다.
- `docs/convention/code-convention.md`: TypeScript 명시 타입, 함수형 컴포넌트, API 응답과 mock data 분리, Tailwind/shadcn primitive 우선 사용 기준을 확인했다.
- `docs/convention/documentation-convention.md`: plan 문서는 `docs/plans/plan-XX-작업명.md`에 한국어로 작성하는 기준을 확인했다.
- `package.json`: 주요 검증 스크립트는 `pnpm lint`, `pnpm build`이다.
- 현재 워크트리: `git status --short` 기준 미커밋 변경 없음.

## 3. 현재 코드 상태

| 파일 | 현재 상태 |
|---|---|
| `lib/api/types.ts` | `DRAIN_STATUS_UPDATED` 타입만 있으며 YOLO/XGBoost 이벤트와 분석 이력 응답 타입이 없다. |
| `lib/websocket/drain-status-socket.ts` | `/ws/drains/status` 단일 endpoint를 사용하지만 `DRAIN_STATUS_UPDATED`만 파싱한다. |
| `lib/api/drains.ts` | 최신 분석 조회는 있으나 분석 이력 REST API 함수는 없다. |
| `lib/api/drain-data.ts` | 상세 진입 시 detail/sensor/risk/latest analysis를 병렬 조회한다. YOLO/XGBoost 이력은 아직 로드하지 않는다. |
| `app/drains/[id]/page.tsx` | 상세 화면에서 CCTV는 최신 이미지 1장만 전달하고, 현재 위험 카드에 주요 수치가 흩어져 보인다. |
| `components/cctv-snapshot-card.tsx` | 썸네일/이전/다음 UI는 있으나 데이터가 1장이라 과거 이미지 이동 검증이 어렵다. 이미지 영역 높이 고정과 이력 표시 방식 보강이 필요하다. |

## 4. 반영할 백엔드 계약

### 4.1 WebSocket

- 기존 endpoint `WS /ws/drains/status`는 유지한다.
- 기존 `DRAIN_STATUS_UPDATED`는 대시보드/상세 최종 상태 갱신용으로 유지한다.
- 신규 `YOLO_RESULT_UPDATED` 이벤트를 수신해 상세 화면의 최신 CCTV 이미지, 막힘 정도, YOLO 상태, confidence score, 분석 시각을 갱신한다.
- 신규 `XGBOOST_RESULT_UPDATED` 이벤트를 수신해 상세 화면의 위험도, 위험 점수, 최종 판단 문구, 참조 `sensorDataId`, `yoloResultId`, `xgboostResultId`를 갱신한다.

### 4.2 REST 이력

우선 통합 endpoint를 1순위로 준비한다.

```text
GET /api/drains/{drain_id}/analysis/history?limit=10
```

응답 타입:

```ts
type DrainAnalysisHistoryResponse = {
    drainId: string;
    yoloResults: YoloResultDto[];
    xgboostResults: XgboostResultDto[];
};
```

백엔드가 분리 endpoint만 제공할 가능성도 있으므로, 구현 시 `lib/api/drains.ts` 안에서 통합 함수의 내부 구현만 바꾸기 쉬운 형태로 둔다.

## 5. 구현 계획

1. 타입 확장
   - `YoloResultDto`, `XgboostResultDto`에 계약 필드 `id`, `drainId`, `capturedAt`, `createdAt`, `sensorDataId`, `yoloResultId`, `evaluatedAt` 등을 추가한다.
   - `DrainAnalysisHistoryResponse`, `YoloResultUpdatedEventDto`, `XgboostResultUpdatedEventDto`, union realtime event 타입을 추가한다.
   - 기존 필드는 optional 또는 null 허용을 사용해 과거 REST 응답과 새 계약 응답을 함께 처리한다.

2. API 함수 추가
   - `getDrainAnalysisHistory(id, { limit })`를 추가한다.
   - 상세 데이터 로드 시 history API를 함께 조회하되, 실패하면 기존 latest analysis와 최신 이미지 1장 표시 흐름은 유지한다.

3. 데이터 어댑터 보강
   - ratio 값을 화면용 percent로 변환하는 기존 흐름을 재사용한다.
   - YOLO/XGBoost 이력을 상세 화면용 view model로 변환한다.
   - 신규 이벤트가 들어오면 같은 `drainId`만 반영하고, 다른 시설 이벤트는 무시한다.

4. WebSocket hook 확장
   - 기존 단일 endpoint는 유지한다.
   - `onStatusUpdated`, `onYoloUpdated`, `onXgboostUpdated` 콜백을 분리한다.
   - 알 수 없는 이벤트 타입이나 필수 필드가 부족한 payload는 무시해 화면이 깨지지 않게 한다.

5. 상세 화면 UI 개편
   - 상세 상단 또는 현재 상태 영역에 “한눈에 들어오는” 요약 컴포넌트를 추가한다.
   - 막힘 정도, 수위, 유속, 위험 점수, 최종 판단을 같은 밀도의 타일/프로그레스 UI로 정리한다.
   - 기존 카드 중복은 줄이고, 시설 정보는 위치/ID/업데이트 시각 중심으로 가볍게 유지한다.

6. AI 판단 정보 탭 구성
   - 외부 패키지 추가 없이 로컬 segmented tab 상태로 구현한다.
   - 탭 후보:
     - `요약`: 최신 위험 판단, 막힘 정도, 수위, 유속, 판단 문구
     - `YOLO`: 이미지, 막힘률, confidence score, yoloStatus, captured/analyzed 시각
     - `XGBoost`: riskScore, riskLevel, finalDecision, 참조 sensor/yolo/xgboost ID, evaluated 시각
     - `이력`: 최근 YOLO/XGBoost 목록
   - shadcn `button`, `badge`, `progress`, `separator`, `tooltip` primitive를 우선 조합한다.

7. CCTV 이미지 이력 UI
   - 사용자 승인 후 아래 추천안 기준으로 구현한다.
   - 기존 `CctvSnapshotCard`의 썸네일 UI는 유지하되, 이미지가 아래 콘텐츠를 밀지 않도록 메인 이미지 영역과 썸네일 스트립 높이를 고정한다.

8. 검증
   - `pnpm lint`
   - `pnpm build`
   - 가능하면 개발 서버에서 `/drains/{id}` 수동 확인
   - 백엔드가 없거나 history API가 미제공이면 mock/latest fallback 상태를 문서화한다.

## 6. 추천 이미지 이력 UI

### 추천안: 고정 높이 CCTV 뷰어 + 가로 썸네일 스트립

상세 왼쪽 CCTV 카드 안에서 메인 이미지 영역을 `aspect-[16/10]` 또는 명시 `h-[260px] md:h-[320px]` 수준으로 고정하고, 아래에는 높이 고정 썸네일 스트립을 가로 스크롤로 둔다.

장점:

- 현재 프로젝트의 카드/썸네일 UI와 가장 잘 이어진다.
- 과거 이미지가 10장 이상이어도 카드 높이가 커지지 않아 지도나 상태 카드가 아래로 밀리지 않는다.
- REST history API가 없을 때도 최신 이미지 1장 + disabled 이전/다음 버튼으로 자연스럽게 fallback 된다.

보완:

- 모바일에서는 썸네일을 `overflow-x-auto`로 처리한다.
- 이미지 비율이 제각각이어도 `object-cover`로 카드 크기를 유지한다.
- 선택한 이미지의 YOLO 정보는 카드 하단의 한 줄 메타 또는 `YOLO` 탭에서 자세히 보여준다.

### 대안: 이미지 히스토리 드로어/모달

기본 상세 화면에는 최신 이미지 1장만 두고, “이력 보기” 버튼을 누르면 모달 또는 드로어에서 과거 이미지를 보여준다.

장점:

- 상세 화면은 가장 안정적으로 유지된다.
- 많은 이미지와 상세 메타를 한 번에 확인하기 좋다.

단점:

- 현재 `components/ui`에 dialog/drawer primitive가 없어 직접 구현 범위가 늘어난다.
- 사용자는 이전 이미지를 보려면 한 번 더 눌러야 한다.

## 7. 사용자 확인 필요 항목

코드 수정 전 아래 방향으로 진행해도 되는지 확인이 필요하다.

1. 이미지 이력 UI는 “고정 높이 CCTV 뷰어 + 가로 썸네일 스트립” 추천안으로 진행한다.
2. 분석 이력 REST는 우선 `GET /api/drains/{drain_id}/analysis/history?limit=10` 통합 endpoint 기준으로 구현한다.
3. 만약 history API가 실패하거나 아직 없으면, 기존 최신 분석 API와 WebSocket 최신 이벤트만으로 화면을 유지한다.
4. 상세 화면 AI 판단 정보는 `요약 / YOLO / XGBoost / 이력` 탭으로 구성한다.

## 8. 완료 기준

- 상세 화면에서 막힘 정도, 수위, 유속, 위험 점수, 최종 판단이 한눈에 보인다.
- `YOLO_RESULT_UPDATED` 수신 시 최신 이미지와 YOLO 분석 정보가 갱신된다.
- `XGBOOST_RESULT_UPDATED` 수신 시 최종 위험 판단과 참조 ID가 갱신된다.
- REST history 응답이 있으면 과거 이미지와 AI 판단 이력이 표시된다.
- REST history 응답이 없거나 실패해도 기존 상세 화면이 깨지지 않는다.
- 이미지 이력 UI가 상세 화면의 다른 카드들을 아래로 과도하게 밀지 않는다.

## 9. 남은 리스크

- 백엔드가 통합 history endpoint 대신 분리 endpoint를 제공하면 API 함수 내부 구현을 조정해야 한다.
- 현재 일부 문서/화면 문자열이 인코딩 깨짐처럼 보이는 부분이 있어, 구현 중 사용자에게 보이는 텍스트를 함께 정리할 필요가 있다.
- XGBoost 결과가 참조한 YOLO 이미지와 최신 YOLO 이미지가 다를 수 있으므로, 탭에서 “최신 YOLO”와 “최종 판단 참조 YOLO”를 구분해 표시해야 할 수 있다.

## 10. 추천 커밋 메시지

제목:

```text
docs: 실시간 분석 계약 반영 상세 화면 개선 계획 추가
```

내용:

```text
- YOLO/XGBoost WebSocket 이벤트와 분석 이력 REST 반영 계획을 정리한다.
- 상세 화면 AI 판단 탭과 요약 컴포넌트 구성 방향을 기록한다.
- 이미지 이력 UI 추천안과 사용자 확인 항목을 문서화한다.
```
