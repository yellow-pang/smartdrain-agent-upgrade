# 백엔드 전달안

## 1. 전달 목적

프론트엔드에서 실시간 분석 결과와 상세 화면 CCTV 이미지 이력을 안정적으로 표시하기 위해 백엔드 WebSocket 이벤트와 REST 이력 API 계약을 요청한다.

현재 프론트는 아래 이벤트만 수신한다.

```text
WS /ws/drains/status
type: DRAIN_STATUS_UPDATED
```

현재 이벤트는 최종 위험 상태 갱신에는 충분하지만, YOLO 이미지, YOLO 분석 결과, XGBoost가 실제 참조한 데이터, 과거 이미지 이력을 정확히 표시하기에는 정보가 부족하다.

## 2. 요청 요약

| 구분         | 요청                                                                    |
| ------------ | ----------------------------------------------------------------------- |
| 최종 상태    | 기존 `DRAIN_STATUS_UPDATED` 유지                                        |
| YOLO 결과    | `YOLO_RESULT_UPDATED` 이벤트 추가 요청                                  |
| XGBoost 결과 | `XGBOOST_RESULT_UPDATED` 이벤트 추가 요청                               |
| 과거 이미지  | WebSocket이 아니라 REST 목록 API로 조회 요청                            |
| endpoint     | 가능하면 기존 `ws://localhost:8000/ws/drains/status` 단일 endpoint 유지 |

## 3. 기존 이벤트 유지 방향

`DRAIN_STATUS_UPDATED`는 대시보드, 지도, 위험 시설 목록, 선택 시설 패널을 빠르게 갱신하는 최종 상태 요약 이벤트로 유지한다.

이미지 URL, YOLO 상태, confidence score, capturedAt은 이 이벤트에 넣지 않는 것을 추천한다. 이 값들은 YOLO 분석 결과의 책임이므로 별도 `YOLO_RESULT_UPDATED` 이벤트 또는 REST 이력 API에서 받는 편이 명확하다.

요청 payload:

```ts
type DrainStatusUpdatedPayload = {
    drainId: string;
    riskLevel: "good" | "caution" | "danger" | "unknown";
    riskScore: number | null;
    waterLevelCm: number | null;
    flowVelocityMps: number | null;
    obstructionRatio: number | null;
    finalDecision: string | null;
    updatedAt: string;
    sensorDataId?: number | null;
    yoloResultId?: number | null;
    xgboostResultId?: number | null;
};
```

예시:

```json
{
    "type": "DRAIN_STATUS_UPDATED",
    "payload": {
        "drainId": "DR-WS-017879",
        "riskLevel": "danger",
        "riskScore": 0.82,
        "waterLevelCm": 120,
        "flowVelocityMps": 0.02,
        "obstructionRatio": 0.76,
        "finalDecision": "막힘률과 수위가 높아 침수 위험이 큽니다.",
        "updatedAt": "2026-06-19T12:43:00+09:00",
        "sensorDataId": 5,
        "yoloResultId": 8,
        "xgboostResultId": 5
    }
}
```

## 4. YOLO 이벤트 요청

YOLO 결과가 저장되면 같은 WebSocket endpoint로 새 이벤트를 발행해주기를 요청한다.

이벤트 이름:

```text
YOLO_RESULT_UPDATED
```

요청 payload:

```ts
type YoloResultUpdatedPayload = {
    drainId: string;
    yoloResultId: number;
    imageUrl: string | null;
    obstructionRatio: number | null;
    confidenceScore: number | null;
    yoloStatus: "clear" | "partially_blocked" | "blocked" | "unknown";
    capturedAt: string | null;
    analyzedAt: string;
    updatedAt: string;
};
```

예시:

```json
{
    "type": "YOLO_RESULT_UPDATED",
    "payload": {
        "drainId": "DR-WS-017879",
        "yoloResultId": 8,
        "imageUrl": "/test-snapshots/drain-001-b.jpg",
        "obstructionRatio": 0.76,
        "confidenceScore": 0.88,
        "yoloStatus": "blocked",
        "capturedAt": "2026-06-19T12:42:00+09:00",
        "analyzedAt": "2026-06-19T12:42:01+09:00",
        "updatedAt": "2026-06-19T12:42:01+09:00"
    }
}
```

프론트 사용 목적:

| 필드                       | 사용 위치             |
| -------------------------- | --------------------- |
| `imageUrl`                 | 상세 CCTV 최신 이미지 |
| `obstructionRatio`         | 막힘 정도             |
| `confidenceScore`          | 상세 분석 정보        |
| `yoloStatus`               | 상세 분석 상태        |
| `capturedAt`, `analyzedAt` | 이미지/분석 시각      |

## 5. XGBoost 이벤트 요청

XGBoost 결과가 저장되면 같은 WebSocket endpoint로 새 이벤트를 발행해주기를 요청한다.

이벤트 이름:

```text
XGBOOST_RESULT_UPDATED
```

요청 payload:

```ts
type XgboostResultUpdatedPayload = {
    drainId: string;
    xgboostResultId: number;
    sensorDataId: number | null;
    yoloResultId: number | null;
    riskLevel: "good" | "caution" | "danger" | "unknown";
    riskScore: number | null;
    finalDecision: string | null;
    evaluatedAt: string;
    updatedAt: string;
};
```

예시:

```json
{
    "type": "XGBOOST_RESULT_UPDATED",
    "payload": {
        "drainId": "DR-WS-017879",
        "xgboostResultId": 5,
        "sensorDataId": 5,
        "yoloResultId": 8,
        "riskLevel": "danger",
        "riskScore": 0.82,
        "finalDecision": "막힘률과 수위가 높아 침수 위험이 큽니다.",
        "evaluatedAt": "2026-06-19T12:43:00+09:00",
        "updatedAt": "2026-06-19T12:43:00+09:00"
    }
}
```

프론트 사용 목적:

| 필드                           | 사용 위치                    |
| ------------------------------ | ---------------------------- |
| `riskLevel`                    | 상태 배지, 지도 마커 색상    |
| `riskScore`                    | 위험 점수, 목록 정렬         |
| `finalDecision`                | 현재 위험 상태 판단 문구     |
| `sensorDataId`, `yoloResultId` | 최종 판단의 원천 데이터 추적 |
| `xgboostResultId`              | 위험 이력 추적               |

## 6. 과거 이미지/분석 이력 REST API 요청

과거 이미지와 분석 이력은 WebSocket으로 전체 목록을 받지 않고 REST API로 조회하는 것을 요청한다.

이유:

| 이유           | 설명                                                                      |
| -------------- | ------------------------------------------------------------------------- |
| 초기 화면 구성 | 사용자가 상세 화면에 늦게 들어와도 과거 이미지 목록을 조회할 수 있어야 함 |
| payload 크기   | WebSocket 이벤트에 이미지 목록 전체를 싣지 않아도 됨                      |
| 새로고침 대응  | 새로고침 후에도 같은 이력을 REST로 다시 구성 가능                         |

추천 endpoint 후보:

```text
GET /api/drains/{drain_id}/analysis/yolo?limit=10
GET /api/drains/{drain_id}/analysis/xgboost?limit=10
```

또는 통합 endpoint:

```text
GET /api/drains/{drain_id}/analysis/history?limit=10
```

프론트가 가장 쓰기 쉬운 통합 응답:

```ts
type DrainAnalysisHistoryResponse = {
    drainId: string;
    yoloResults: YoloResultDto[];
    xgboostResults: XgboostResultDto[];
};
```

YOLO 목록 item:

```ts
type YoloResultDto = {
    id: number;
    drainId: string;
    imageUrl: string | null;
    obstructionRatio: number | null;
    confidenceScore: number | null;
    yoloStatus: "clear" | "partially_blocked" | "blocked" | "unknown";
    capturedAt: string | null;
    analyzedAt: string;
    createdAt: string;
};
```

XGBoost 목록 item:

```ts
type XgboostResultDto = {
    id: number;
    drainId: string;
    sensorDataId: number | null;
    yoloResultId: number | null;
    riskLevel: "good" | "caution" | "danger" | "unknown";
    riskScore: number | null;
    finalDecision: string | null;
    evaluatedAt: string;
    createdAt: string;
};
```

정렬 요청:

```text
최신순 정렬
limit query 지원
```

## 7. 백엔드 확인 질문

| 번호 | 질문                                                                                                  | 이유                                                                  |
| ---- | ----------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| 1    | `/ws/drains/status` 단일 endpoint에서 이벤트 `type`만 확장해도 되는가?                                | 프론트는 단일 WebSocket 연결을 유지하고 싶음                          |
| 2    | YOLO 저장 직후 `YOLO_RESULT_UPDATED` broadcast를 추가할 수 있는가?                                    | 상세 CCTV 최신 이미지와 막힘 분석 실시간 반영 필요                    |
| 3    | XGBoost 저장 직후 `XGBOOST_RESULT_UPDATED` broadcast를 추가할 수 있는가?                              | 위험 판단과 원천 데이터 ID 추적 필요                                  |
| 4    | `DRAIN_STATUS_UPDATED.obstructionRatio`는 XGBoost 요청의 `yoloResultId` 기준인가, 최신 YOLO 기준인가? | 현재 테스트에서 XGBoost 참조 YOLO와 최신 YOLO 기준이 어긋날 수 있었음 |
| 5    | XGBoost 결과의 `yoloResultId`는 실제 모델 입력에 사용한 YOLO 결과 ID가 맞는가?                        | 화면 이미지와 최종 판단 기준 불일치 방지                              |
| 6    | 과거 이미지용 YOLO result list API를 제공할 수 있는가?                                                | 상세 CCTV 이전/다음 이미지 이동에 필요                                |
| 7    | YOLO/XGBoost 이력 목록은 최신순 정렬과 `limit` query를 지원할 수 있는가?                              | 상세 화면 이력 UI 구성 필요                                           |
| 8    | `POST /api/drains` 응답에 후속 POST용 내부 숫자 ID를 추가할 수 있는가?                                | Swagger 수동 테스트에서 `drainId` 입력값 확인이 어려움                |
| 9    | 한글 주소와 `finalDecision` 인코딩 깨짐을 확인할 수 있는가?                                           | 실제 화면 문구 품질 문제                                              |

## 8. 프론트 기대 동작

백엔드 계약이 확정되면 프론트는 아래 방식으로 사용할 예정이다.

1. 대시보드는 `DRAIN_STATUS_UPDATED` 기준으로 최종 상태를 갱신한다.
2. 상세 화면은 최초 진입 시 REST history API로 최근 YOLO 이미지 목록을 조회한다.
3. 상세 화면은 `YOLO_RESULT_UPDATED` 수신 시 최신 이미지 1건을 이미지 목록 맨 앞에 추가한다.
4. 상세 화면은 `XGBOOST_RESULT_UPDATED` 수신 시 현재 위험 상태와 위험 이력을 갱신한다.
5. REST history API가 없으면 과거 이미지 이동은 보류하고 최신 이미지 1장 갱신만 처리한다.

## 9. 결론

백엔드에 요청하는 최종 방향:

```text
DRAIN_STATUS_UPDATED는 최종 상태 요약 이벤트로 유지한다.
YOLO 이미지와 분석 결과는 YOLO_RESULT_UPDATED로 분리한다.
XGBoost 판단 결과와 참조 ID는 XGBOOST_RESULT_UPDATED로 분리한다.
과거 이미지/분석 이력은 REST 목록 API로 조회한다.
```
