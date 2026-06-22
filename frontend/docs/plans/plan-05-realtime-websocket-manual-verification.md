# 05_realtime websocket manual verification 계획

## 1. 작업 개요

| 항목 | 내용 |
|---|---|
| 브랜치 | `test/realtime-websocket-verification` |
| 작업 범위 | `/frontend` 내부 문서화 및 수동 테스트 준비 |
| 목적 | 자동/CLI로 확인한 WebSocket 결과를 실제 브라우저 화면에서 수동 재검증 |
| 기준 endpoint | `ws://localhost:8000/ws/drains/status` |
| 기준 이벤트 | `POST /api/analysis/xgboost` 후 발생하는 `DRAIN_STATUS_UPDATED` |
| 백엔드 수정 | 하지 않음. 필요한 변경은 확인 필요 항목으로만 기록 |

이번 계획은 이미 진행한 CLI 기반 통합 테스트 결과를 바탕으로, 사용자가 실제 브라우저와 Swagger에서 수동으로 확인할 항목을 정리한다. 현재 화면에서는 과거 이미지 이동과 이미지 크기/레이아웃 문제가 남아 있으므로, 수동 테스트 완료 기준을 “WebSocket 이벤트 수신과 최신 상태 반영 확인”으로 좁히고, 과거 이미지 이력 UI는 후속 개선 대상으로 분리한다.

## 2. 현재 DB 기준 테스트 데이터

2026-06-19 12:30 KST 기준 `GET /api/drains`에서 확인한 데이터는 아래와 같다.

| 시설 ID | 상태 | 위험 점수 | 막힘 정도 | 수위 | 유량 | 비고 |
|---|---:|---:|---:|---:|---:|---|
| `DR-INT-001` | `danger` | `0.781` | `0.88` | `85.0` | `0.05` | 기존 통합 테스트 데이터 |
| `DR-WS-017879` | `caution` | `0.739` | `0.22` | `92.0` | `0.03` | 이번 WebSocket 검증 데이터 |

수동 테스트 기본 대상은 `DR-WS-017879`로 한다.

| 항목 | 현재 값 |
|---|---|
| 상세 URL | `http://localhost:3000/drains/DR-WS-017879` |
| 최신 imageUrl | `/test-snapshots/drain-001-c.jpg` |
| 센서 데이터 | 1건 |
| 위험 이력 | 1건 |
| 최신 YOLO id | `4` |
| 최신 XGBoost id | `2` |
| XGBoost가 참조한 YOLO id | `3` |

주의:

현재 `DR-WS-017879`는 센서 이력과 위험 이력이 각각 1건뿐이다. 그래서 차트의 추세, 위험 이력 목록의 다건 정렬, 과거 이미지 이동까지 검증하려면 수동 테스트 중 추가 데이터를 더 만들어야 한다.

## 3. 수동 테스트 준비

| 준비 항목 | 확인 방법 | 기대 결과 |
|---|---|---|
| Backend | `http://localhost:8000/` 접속 | `success: true`, `data.status: ok` |
| Swagger | `http://localhost:8000/docs` 접속 | API 문서 표시 |
| Frontend | `http://localhost:3000` 접속 | 대시보드 표시 |
| 상세 화면 | `http://localhost:3000/drains/DR-WS-017879` 접속 | 상세 화면 표시 |
| 테스트 이미지 | `http://localhost:3000/test-snapshots/drain-001-c.jpg` 접속 | 이미지 표시 |
| DevTools Network | WS 필터에서 `/ws/drains/status` 확인 | 101 또는 연결 상태 확인 |

## 4. Swagger 수동 입력 양식

현재 DB에 있는 `DR-WS-017879`의 내부 숫자 ID는 이전 테스트 흐름상 `2`로 사용했다. 백엔드 응답에는 이 내부 숫자 ID가 직접 노출되지 않으므로, 새 시설을 만들면 같은 방식으로 목록 순서나 응답 로그를 보고 내부 ID를 추정해야 한다.

### 4.1 센서 데이터 추가

Endpoint:

```text
POST /api/sensor-data
```

Request body:

```json
{
  "drainId": 2,
  "waterLevelCm": 120,
  "flowVelocityMps": 0.02,
  "measuredAt": "2026-06-19T12:40:00+09:00"
}
```

기대 결과:

| 확인 항목 | 기대값 |
|---|---|
| status | `201` |
| `success` | `true` |
| `data.drainId` | `DR-WS-017879` |
| `data.waterLevelCm` | 입력한 값 |
| `data.id` | 다음 XGBoost 요청의 `sensorDataId` 후보 |

### 4.2 YOLO 결과 여러 장 추가

Endpoint:

```text
POST /api/analysis/yolo
```

Request body A:

```json
{
  "drainId": 2,
  "imageUrl": "/test-snapshots/drain-001-a.jpg",
  "obstructionRatio": 0.35,
  "confidenceScore": 0.78,
  "yoloStatus": "partially_blocked",
  "capturedAt": "2026-06-19T12:41:00+09:00"
}
```

Request body B:

```json
{
  "drainId": 2,
  "imageUrl": "/test-snapshots/drain-001-b.jpg",
  "obstructionRatio": 0.76,
  "confidenceScore": 0.88,
  "yoloStatus": "blocked",
  "capturedAt": "2026-06-19T12:42:00+09:00"
}
```

Request body C:

```json
{
  "drainId": 2,
  "imageUrl": "/test-snapshots/drain-001-c.jpg",
  "obstructionRatio": 0.18,
  "confidenceScore": 0.82,
  "yoloStatus": "clear",
  "capturedAt": "2026-06-19T12:43:00+09:00"
}
```

기대 결과:

| 확인 항목 | 기대값 |
|---|---|
| status | 각 요청 `201` |
| `data.imageUrl` | 요청한 `/test-snapshots/*.jpg` |
| `data.id` | XGBoost 요청에 넣을 `yoloResultId` 후보 |
| 최신 분석 조회 | 가장 늦은 `capturedAt` 또는 백엔드 latest 기준 imageUrl 표시 |

### 4.3 XGBoost 실행 및 WebSocket 이벤트 확인

Endpoint:

```text
POST /api/analysis/xgboost
```

Request body:

```json
{
  "drainId": 2,
  "sensorDataId": 2,
  "yoloResultId": 4
}
```

`sensorDataId`, `yoloResultId`는 Swagger 응답에서 새로 받은 값으로 바꿔 넣는다.

기대 결과:

| 확인 항목 | 기대값 |
|---|---|
| status | `201` |
| `data.riskLevel` | `good`, `caution`, `danger`, `unknown` 중 하나 |
| WebSocket event | `DRAIN_STATUS_UPDATED` |
| payload drainId | `DR-WS-017879` |
| 대시보드 | 지도/목록/선택 패널 값 변경 |
| 상세 화면 | 현재 위험 상태 값 변경 |

## 5. 수동 화면 확인 양식

| 구분 | 확인 항목 | 기대 결과 | 실제 결과 | 상태 |
|---|---|---|---|---|
| Dashboard | WebSocket 상태 chip | `실시간 연결됨` 표시 |  | 확인 필요 |
| Dashboard | XGBoost 실행 직후 상태 변경 | 해당 시설의 위험도/막힘 정도/수위/유량 갱신 |  | 확인 필요 |
| Dashboard | 지도 마커 | 위험도 색상 변경 |  | 확인 필요 |
| Dashboard | 위험 시설 목록 | 위험도순 재정렬 |  | 확인 필요 |
| Dashboard | 선택 시설 패널 | 선택된 `DR-WS-017879` 값 부분 갱신 |  | 확인 필요 |
| Detail | 상세 WebSocket 상태 | 연결 상태가 정상 표시 |  | 확인 필요 |
| Detail | 현재 위험 상태 | XGBoost 결과 기준 값 갱신 |  | 확인 필요 |
| Detail | 센서 차트 | 새 센서 데이터가 반영되는지 확인 |  | 확인 필요 |
| Detail | CCTV 최신 이미지 | 최신 `imageUrl` 표시 |  | 부분 확인 |
| Detail | 과거 이미지 이동 | 이전/다음 버튼으로 과거 이미지가 바뀌는지 확인 | 현재 정상 검증 어려움 | 보류 |
| Detail | 과거 위험 이력 | 새 XGBoost 실행 후 이력 행이 추가되는지 확인 |  | 확인 필요 |
| Layout | 이미지 크기 | CCTV/과거 이미지가 다른 카드나 지도 영역을 밀지 않음 | 현재 아쉬움 있음 | 실패 |
| Error | 잘못된 imageUrl | placeholder로 대체 표시 |  | 확인 필요 |
| Error | WebSocket 끊김 | `reconnecting` 또는 `error` 표시 |  | 확인 필요 |

## 6. 현재 놓치기 쉬운 테스트 항목

| 항목 | 왜 필요한가 | 확인 방법 |
|---|---|---|
| WebSocket reconnect | 서버 재시작/일시 중단 시 화면이 멈추지 않는지 확인 | 백엔드 재시작 후 chip 상태 변화 확인 |
| 잘못된 이벤트 payload | 프론트 parser가 무시하고 화면이 깨지지 않는지 확인 | 백엔드 지원 없으면 보류 |
| 다른 시설 이벤트 | 현재 상세 화면 ID와 다른 `drainId` 이벤트가 상세 화면을 바꾸지 않는지 확인 | `DR-INT-001` 대상으로 XGBoost 실행 |
| 목록 정렬 변화 | 위험도 순위가 실제로 바뀌는지 확인 | `DR-WS-017879`를 `danger`에 가까운 값으로 만들기 |
| 여러 센서 포인트 | 차트가 1점이 아니라 추세로 보이는지 확인 | 센서 데이터 3건 이상 생성 |
| 여러 위험 이력 | 최근 7일 이력 카드가 여러 행을 처리하는지 확인 | XGBoost 2회 이상 실행 |
| 이미지 fallback | 깨진 URL에서 placeholder가 표시되는지 확인 | YOLO imageUrl에 없는 경로 입력 |
| 모바일 화면 | 이미지/카드가 세로 화면에서 겹치지 않는지 확인 | 브라우저 responsive mode |
| 새로고침 후 상태 유지 | WebSocket으로 갱신된 값이 REST 조회에도 유지되는지 확인 | XGBoost 후 새로고침 |
| 시간 표시 | ISO 문자열이 화면에서 읽기 쉬운 형식인지 확인 | 상세 카드와 이력 카드 확인 |

## 7. 과거 이미지 이력 UI 후속 개선 방향

현재 상세 화면의 CCTV 카드는 썸네일/이전/다음 UI가 있지만, 실제 데이터는 최신 이미지 1장만 전달되는 구조다. 따라서 사용자가 여러 YOLO 이미지를 저장해도 화면에서 과거 이미지로 이동하는 테스트는 정상 완료로 보기 어렵다.

후속 UI 개선 때 함께 볼 항목:

| 개선 항목 | 방향 |
|---|---|
| 이미지 이력 데이터 | 백엔드가 YOLO 결과 목록 또는 이미지 history endpoint 제공 필요 |
| 상세 화면 snapshots | 최신 1장이 아니라 여러 이미지 배열을 `CctvSnapshotCard`에 전달 |
| 이미지 크기 | 큰 이미지가 왼쪽 컬럼 높이를 과도하게 늘려 지도/상태 영역을 밀지 않도록 max-height 적용 |
| 썸네일 영역 | 썸네일은 고정 높이와 `object-cover`로 제한 |
| 좌우 이동 버튼 | 이미지가 1장일 때는 버튼 숨김 또는 disabled 상태를 명확히 표시 |
| 레이아웃 | CCTV, 지도, 상태 카드가 서로 밀리지 않도록 desktop grid 높이 제한 검토 |

## 8. 수동 테스트 완료 기준

이번 수동 테스트는 아래를 만족하면 완료로 본다.

1. 대시보드와 상세 화면에서 WebSocket 연결 상태가 `connected`에 해당하는 UI로 보인다.
2. Swagger에서 XGBoost를 실행하면 `DRAIN_STATUS_UPDATED`가 발생한다.
3. 대시보드 지도, 위험 시설 목록, 선택 시설 패널 중 최소 2개 이상에서 값 변경을 눈으로 확인한다.
4. 상세 화면의 현재 위험 상태가 XGBoost 결과 기준으로 바뀐다.
5. 최신 imageUrl 표시 기준은 확인하되, 과거 이미지 이동은 “현재 구조상 보류”로 기록한다.
6. 이미지 크기 때문에 레이아웃이 밀리는 문제는 후속 UI 개선 이슈로 남긴다.
7. 실패/보류 항목은 `step-06-realtime-websocket-verification.md`에 실제 결과로 보강한다.

## 9. 추천 커밋 메시지

제목:

```text
docs: 실시간 WebSocket 수동 검증 계획 정리
```

내용:

```text
- 현재 DB 데이터 기준 수동 테스트 입력 양식을 정리한다.
- WebSocket 이벤트와 화면 갱신 확인 항목을 대시보드와 상세 화면으로 나눈다.
- 과거 이미지 이력과 이미지 크기 문제를 후속 UI 개선 항목으로 기록한다.
```
