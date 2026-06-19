# 08 실시간 분석 계약 반영 상세 화면 개선 작업 기록

## 1. 작업 목적

이번 작업은 백엔드 추가 계약에 맞춰 프론트엔드 상세 화면이 YOLO 이미지 분석 결과와 XGBoost 최종 판단 정보를 더 명확하게 보여주도록 바꾸는 것이 목적이다.

기존 상세 화면은 최신 위험 상태와 CCTV 이미지 1장을 보여주는 데 초점이 있었다. 그러나 새 계약에서는 `DRAIN_STATUS_UPDATED` 외에 `YOLO_RESULT_UPDATED`, `XGBOOST_RESULT_UPDATED`, 분석 이력 REST API가 추가될 예정이므로, 화면도 단순 상태 표시에서 “실시간 분석 대시보드”에 가까운 구조가 필요해졌다.

## 2. 작업 전 문제

| 구분         | 기존 상태                                   | 문제                                                                              |
| ------------ | ------------------------------------------- | --------------------------------------------------------------------------------- |
| WebSocket    | `DRAIN_STATUS_UPDATED`만 처리               | YOLO 이미지, 막힘률, confidence score, XGBoost 참조 ID를 실시간 반영할 수 없었다. |
| REST API     | 최신 분석만 조회                            | 과거 CCTV 이미지와 분석 이력을 상세 화면에서 구성하기 어려웠다.                   |
| 상세 화면    | CCTV, 센서 차트, 현재 위험 카드가 분리 표시 | 사용자가 막힘 정도, 수위, 유속, 위험 점수, 최종 판단을 한눈에 보기 어려웠다.      |
| AI 판단 정보 | 현재 위험 상태 카드 안에 일부 값만 표시     | YOLO와 XGBoost가 각각 어떤 근거로 판단했는지 분리해서 확인하기 어려웠다.          |
| 이미지 이력  | 썸네일 UI는 있으나 최신 이미지 1장만 전달   | 과거 이미지가 들어오면 카드 높이가 늘어나거나 주변 UI를 밀 가능성이 있었다.       |

## 3. 반영한 계약

### WebSocket

기존 단일 endpoint는 유지한다.

```text
WS /ws/drains/status
```

처리 이벤트를 아래처럼 확장했다.

| 이벤트                   | 프론트 사용 목적                                                       |
| ------------------------ | ---------------------------------------------------------------------- |
| `DRAIN_STATUS_UPDATED`   | 대시보드와 상세 화면의 최종 위험 상태 요약 갱신                        |
| `YOLO_RESULT_UPDATED`    | 최신 CCTV 이미지, 막힘률, YOLO 상태, confidence score 갱신             |
| `XGBOOST_RESULT_UPDATED` | 위험 상태, 위험 점수, 최종 판단 문구, 참조 sensor/yolo/xgboost ID 갱신 |

### REST 이력

분석 이력은 통합 endpoint를 우선 기준으로 추가했다.

```text
GET /api/drains/{drain_id}/analysis/history?limit=10
```

이 API가 실패하거나 아직 백엔드에 없더라도 상세 화면 전체가 실패하지 않도록, history 요청만 별도로 실패 허용 처리했다.

## 4. 주요 변경 파일

| 파일                                                         | 변경 내용                                                         |
| ------------------------------------------------------------ | ----------------------------------------------------------------- |
| `docs/plans/plan-06-realtime-analysis-contract-detail-ui.md` | 코드 수정 전 구현 계획과 사용자 확인 항목을 기록                  |
| `lib/api/types.ts`                                           | YOLO/XGBoost 이벤트 타입, 분석 이력 응답 타입, 확장 DTO 필드 추가 |
| `lib/api/drains.ts`                                          | `getDrainAnalysisHistory` API 함수 추가                           |
| `lib/api/drain-data.ts`                                      | 상세 진입 시 분석 이력 조회를 추가하고 실패 시 fallback 유지      |
| `lib/api/mock-responses.ts`                                  | 백엔드 없이 UI 확인이 가능하도록 mock YOLO/XGBoost 이력 추가      |
| `lib/websocket/drain-status-socket.ts`                       | 단일 WebSocket 연결에서 세 이벤트를 파싱하고 콜백 분기            |
| `components/cctv-snapshot-card.tsx`                          | 고정 높이 CCTV 뷰어, 가로 썸네일 스트립, YOLO 메타 오버레이 추가  |
| `app/drains/[id]/page.tsx`                                   | 분석 요약 카드, AI 판단 탭, 실시간 YOLO/XGBoost 상세 반영 추가    |

## 5. 왜 이렇게 바꿨는가

### 5.1 WebSocket endpoint는 유지하고 이벤트 type만 확장

백엔드 계약 문서에서 가능한 한 `ws://localhost:8000/ws/drains/status` 단일 endpoint를 유지하는 방향을 제안했다. 프론트에서도 이 방향이 더 단순하다.

이유:

- 대시보드와 상세 화면이 WebSocket 연결을 여러 개 만들 필요가 없다.
- 기존 `DRAIN_STATUS_UPDATED` 흐름을 깨지 않는다.
- 이벤트가 추가되어도 `type` 분기만 늘리면 된다.

따라서 `useDrainStatusSocket`은 endpoint를 바꾸지 않고 `onStatusUpdated`, `onYoloUpdated`, `onXgboostUpdated` 콜백만 추가했다.

### 5.2 분석 이력 API는 실패해도 화면을 유지

분석 이력 REST API는 아직 백엔드 제공 형태가 바뀔 수 있다. 그래서 상세 화면 진입 시 history API를 함께 요청하되, 이 요청이 실패해도 기존 상세 조회와 최신 분석 조회는 계속 사용하게 했다.

이유:

- 백엔드가 history API를 아직 제공하지 않아도 상세 화면이 깨지지 않는다.
- 현재 MVP 테스트 중인 최신 분석 표시 흐름을 유지할 수 있다.
- 나중에 분리 endpoint로 바뀌어도 `getDrainAnalysisHistory` 함수 내부만 조정하면 된다.

### 5.3 상세 화면 상단에 분석 요약 카드 추가

사용자가 상세 화면에 들어왔을 때 가장 먼저 봐야 하는 정보는 “지금 이 배수구가 위험한가, 왜 위험한가”이다.

그래서 막힘 정도, 수위, 유속, 위험 점수, 최종 판단을 상단 요약 카드로 묶었다.

이유:

- 기존처럼 차트와 카드 사이에 값이 흩어져 있으면 빠른 판단이 어렵다.
- 대시보드 성격의 상세 화면이라는 요청에 맞게 핵심 지표를 한 화면 상단에서 보여줄 수 있다.
- YOLO와 XGBoost가 들어오면 요약 카드 값도 즉시 업데이트된다.

### 5.4 AI 판단 정보는 탭으로 분리

YOLO와 XGBoost는 역할이 다르다.

- YOLO: 이미지 기반 막힘 상태와 confidence score
- XGBoost: 센서/YOLO 결과를 바탕으로 한 최종 위험 판단

따라서 한 카드에 모두 섞지 않고 `요약 / YOLO / XGBoost / 이력` 탭으로 나눴다.

이유:

- 사용자가 “이미지 분석 결과”와 “최종 위험 판단 결과”를 구분해서 볼 수 있다.
- XGBoost가 참조한 `sensorDataId`, `yoloResultId`를 별도로 보여줄 수 있다.
- 향후 백엔드가 참조 YOLO와 최신 YOLO가 다를 때도 UI 확장이 쉽다.

### 5.5 이미지 이력은 고정 높이 뷰어로 처리

사용자 확인을 받은 추천안대로, CCTV 카드는 고정 높이 메인 이미지 영역과 가로 썸네일 스트립으로 바꿨다.

이유:

- 과거 이미지가 10장 이상 들어와도 카드 높이가 계속 늘어나지 않는다.
- 아래 지도나 상태 카드가 이미지 이력 때문에 밀리지 않는다.
- 기존 `CctvSnapshotCard`의 이전/다음 버튼과 썸네일 구조를 재사용할 수 있다.
- 새 패키지나 dialog/drawer 구현 없이 현재 UI 안에서 해결할 수 있다.

## 6. 실시간 반영 흐름

### YOLO 이벤트 수신

1. 현재 상세 화면의 `drain.id`와 이벤트 `payload.drainId`가 같은지 확인한다.
2. 이벤트 payload를 `YoloResultDto` 형태로 변환한다.
3. 최신 YOLO 결과를 `analysis.yoloResult`에 반영한다.
4. `analysisHistory.yoloResults` 맨 앞에 추가하고 같은 ID는 중복 제거한다.
5. 막힘률이 있으면 상세 drain의 `blockage`도 갱신한다.
6. CCTV 카드와 YOLO 탭, 요약 카드가 함께 갱신된다.

### XGBoost 이벤트 수신

1. 현재 상세 화면의 `drain.id`와 이벤트 `payload.drainId`가 같은지 확인한다.
2. 이벤트 payload를 `XgboostResultDto` 형태로 변환한다.
3. 최신 XGBoost 결과를 `analysis.xgboostResult`에 반영한다.
4. `analysisHistory.xgboostResults` 맨 앞에 추가하고 같은 ID는 중복 제거한다.
5. 최종 위험 상태, 판단 문구, 위험 이력 목록을 갱신한다.
6. 상태 배지, 요약 카드, XGBoost 탭, 위험 이력이 함께 갱신된다.

## 7. fallback 기준

| 상황                            | 처리                                      |
| ------------------------------- | ----------------------------------------- |
| `NEXT_PUBLIC_API_BASE_URL` 없음 | 기존처럼 mock 데이터 사용                 |
| 상세 API 실패                   | mock 상세 데이터 fallback                 |
| history API 실패                | 상세 화면은 유지하고 최신 분석 API만 사용 |
| YOLO 이미지 URL 없음            | placeholder 이미지 표시                   |
| 이벤트 type을 알 수 없음        | 무시하고 화면 유지                        |
| 다른 drainId 이벤트 수신        | 현재 상세 화면에는 반영하지 않음          |

## 8. 검증 결과

| 명령어                                  | 결과      | 비고                                            |
| --------------------------------------- | --------- | ----------------------------------------------- |
| `cmd.exe /c pnpm.cmd lint`              | 통과      | 기존 `FallbackImage`의 `<img>` warning 1개 유지 |
| `cmd.exe /c pnpm.cmd build`             | 통과      | Next.js production build 성공                   |
| `cmd.exe /c pnpm.cmd exec tsc --noEmit` | 통과      | TypeScript 타입 검증 성공                       |
| 사용자 실행 확인                        | 확인 완료 | 사용자가 실행 후 확인했다고 전달                |

PowerShell에서 직접 `pnpm lint`를 실행하면 실행 정책 때문에 `pnpm.ps1`이 막혔다. 그래서 Windows 실행 파일인 `pnpm.cmd`를 사용했다.

## 9. 남은 리스크

- 백엔드가 통합 history endpoint 대신 분리 endpoint를 제공하면 `getDrainAnalysisHistory` 내부 구현을 조정해야 한다.
- 현재 일부 기존 문서/터미널 출력에서 한글이 깨져 보이는 파일이 있어, 이후 문서/화면 문구 정리 작업을 별도로 할 수 있다.
- 실제 WebSocket으로 신규 YOLO/XGBoost 이벤트가 들어오는지는 백엔드 구현 완료 후 다시 통합 테스트가 필요하다.
- XGBoost가 참조한 YOLO 결과와 최신 YOLO 결과가 다를 경우, 화면에서 “최신 YOLO”와 “최종 판단 참조 YOLO”를 더 명확히 구분하는 보강이 필요할 수 있다.

## 10. 다음 작업 제안

| 작업                              | 이유                                                                                   |
| --------------------------------- | -------------------------------------------------------------------------------------- |
| 백엔드 신규 이벤트 통합 테스트    | 실제 `YOLO_RESULT_UPDATED`, `XGBOOST_RESULT_UPDATED` payload가 계약과 맞는지 확인 필요 |
| history endpoint 실제 응답 테스트 | 프론트 fallback이 아닌 실제 과거 이미지 이력 표시 확인 필요                            |
| 상세 화면 문구/시간 표시 정리     | ISO 시간을 더 읽기 쉬운 한국어 표기로 통일 가능                                        |
| 참조 YOLO 구분 표시               | XGBoost 판단에 사용한 이미지와 최신 이미지가 다를 때 혼동 방지                         |

## 11. 추천 커밋 메시지

제목:

```text
feat: 실시간 분석 계약 기반 상세 화면 개선
```

내용:

```text
- YOLO/XGBoost WebSocket 이벤트 타입과 수신 처리를 추가한다.
- 분석 이력 REST API 조회와 mock history 응답을 추가한다.
- 상세 화면에 분석 요약 카드와 AI 판단 정보 탭을 구성한다.
- CCTV 이미지 이력을 고정 높이 뷰어와 가로 썸네일 스트립으로 표시한다.
- 실시간 YOLO/XGBoost 이벤트 수신 시 상세 화면 이력과 판단 정보를 갱신한다.
- 실시간 분석 계약 반영 계획, Step, PR 문서를 추가한다.
```
