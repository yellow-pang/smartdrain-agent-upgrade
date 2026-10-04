# 10 AI-프론트-백엔드 통합 테스트 결과

## 1. 작업 목적

이번 테스트는 프론트-백엔드 통합이 완료된 상태에서 AI Service까지 포함한 비동기 분석 흐름이 실제 실행 환경에서 동작하는지 확인하는 것이 목적이다.

검증 대상 흐름은 다음과 같다.

```text
Backend POST /api/analysis/async-run
→ AI Service POST /ai/analysis/run
→ AI Service callback
→ Backend DB 저장
→ WebSocket 이벤트 발행
→ Frontend REST/화면 반영
```

## 2. 테스트 환경

| 항목              | 값                                                     |
| ----------------- | ------------------------------------------------------ |
| 테스트 일자       | 2026-06-19                                             |
| 브랜치            | `test/be-fe-ai-integration-test`                       |
| Backend URL       | `http://localhost:8000`                                |
| AI Service URL    | `http://localhost:9000`                                |
| Frontend URL      | `http://localhost:3000`                                |
| 대표 테스트 drain | `DR-004`                                               |
| 기준 계획 문서    | `docs/plans/plan-08-ai-front-back-integration-test.md` |
| 테스트 데이터     | `docs/test/ai-front-back-integration/test-data.json`   |

## 3. 테스트 결과 요약

| 구분                | 결과 | 확인 내용                                                                   |
| ------------------- | ---- | --------------------------------------------------------------------------- |
| AI Service pytest   | 통과 | `45 passed`                                                                 |
| Backend health      | 통과 | `GET /` 200                                                                 |
| AI Service docs     | 통과 | `GET /docs` 200                                                             |
| Frontend dashboard  | 통과 | `GET /` 200                                                                 |
| Backend async-run   | 통과 | `POST /api/analysis/async-run` 성공                                         |
| AI callback 저장    | 통과 | YOLO/XGBoost 결과가 analysis history에 추가됨                               |
| 최신 분석 조회      | 통과 | latest API가 최신 YOLO/XGBoost 결과 반환                                    |
| 위험 이력 조회      | 통과 | risk history에 최신 XGBoost 결과 추가                                       |
| 상세 API            | 통과 | `GET /api/drains/DR-004`가 최신 분석 결과 포함                              |
| 상세 화면 접근      | 통과 | `GET /drains/DR-004` 200                                                    |
| 잘못된 drainId      | 통과 | `DRAIN_NOT_FOUND` 반환                                                      |
| WebSocket 자동 수신 | 보류 | 연결 `Open`은 확인했지만 자동 스크립트에서 메시지 본문 수신은 확인하지 못함 |

## 4. 실행한 자동 테스트

### 4.1 AI Service 테스트

명령어:

```powershell
.\.venv\Scripts\python.exe -m pytest ai_service
```

결과:

```text
45 passed in 0.94s
```

확인 범위:

| 범위                   | 결과 |
| ---------------------- | ---- |
| fake YOLO predictor    | 통과 |
| analysis flow          | 통과 |
| async API contract     | 통과 |
| HTTP analysis endpoint | 통과 |
| callback flow          | 통과 |
| callback sender        | 통과 |
| XGBoost contract       | 통과 |

## 5. Backend-AI 통합 smoke test

명령어:

```powershell
$body = @{
    drainId = "DR-004"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri http://localhost:8000/api/analysis/async-run `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

대표 응답:

```json
{
  "success": true,
  "data": {
    "requestId": "REQ_20260619090023851203_4",
    "jobId": "AI_JOB_REQ_20260619090023851203_4",
    "drainId": "DR-004",
    "status": "processing",
    "sensorSummary": {
      "waterLevelCm": 85.0,
      "flowVelocityMps": 0.05,
      "measuredAt": "2026-06-19T16:39:59.705222+09:00"
    }
  }
}
```

판단:

백엔드가 최신 센서 데이터를 기준으로 AI Service에 분석 요청을 보내고, request/job 식별값을 정상 반환했다.

## 6. callback 저장 확인

확인 API:

```text
GET /api/drains/DR-004/analysis/history?limit=3
GET /api/drains/DR-004/analysis/latest
GET /api/drains/DR-004/risk-history?limit=3
```

확인 결과:

| 항목              | 최신 값              |
| ----------------- | -------------------- |
| 최신 YOLO ID      | `10`                 |
| 최신 XGBoost ID   | `9`                  |
| 최신 yoloResultId | `10`                 |
| riskLevel         | `danger`             |
| riskScore         | `0.85`               |
| finalDecision     | `dispatch_required`  |
| imageUrl          | `ai-server://mock/4` |

판단:

AI Service callback 결과가 백엔드 DB에 저장되고, latest/history/risk-history API에서 조회된다.

## 7. 프론트 표시 smoke test

확인 항목:

| 항목                                      | 결과                        |
| ----------------------------------------- | --------------------------- |
| `GET http://localhost:3000`               | 200                         |
| `GET http://localhost:3000/drains/DR-004` | 200                         |
| `GET /api/dashboard/summary`              | 최신 업데이트 시각 포함     |
| `GET /api/drains/DR-004`                  | 최신 YOLO/XGBoost 결과 포함 |

상세 API에서 확인한 최신 값:

| 항목             | 값                  |
| ---------------- | ------------------- |
| riskLevel        | `danger`            |
| riskScore        | `0.85`              |
| obstructionRatio | `0.061`             |
| waterLevelCm     | `85.0`              |
| flowVelocityMps  | `0.05`              |
| finalDecision    | `dispatch_required` |

판단:

프론트 서버와 상세 화면 경로가 정상 응답하고, 백엔드 상세 API는 AI 분석 결과를 포함해 반환한다.

## 8. 오류 케이스 확인

잘못된 drainId로 async-run을 호출했다.

```powershell
$body = @{
    drainId = "DR-NOT-FOUND"
} | ConvertTo-Json
```

결과:

```json
{
  "success": false,
  "error": {
    "code": "DRAIN_NOT_FOUND",
    "message": "Drain not found"
  }
}
```

판단:

존재하지 않는 drain 요청은 명확한 오류 코드로 실패한다.

## 9. WebSocket 자동 확인 결과

PowerShell/.NET WebSocket 클라이언트로 `/ws/drains/status` 연결을 시도했다.

확인된 것:

```text
WS_CONNECTED=Open
```

보류한 것:

자동 스크립트에서 `YOLO_RESULT_UPDATED`, `XGBOOST_RESULT_UPDATED`, `DRAIN_STATUS_UPDATED` 메시지 본문을 안정적으로 수신하지 못했다.

판단:

WebSocket endpoint 연결은 가능하지만, 이벤트 메시지 수신은 브라우저 DevTools에서 수동으로 확인하는 항목으로 남긴다.

### 9.1 사용자가 직접 확인할 WebSocket 수동 테스트

자동화에서 실패한 부분은 WebSocket 메시지 본문 수신이다. 아래 절차로 브라우저에서 직접 확인한다.

준비:

| 서버       | URL                     |
| ---------- | ----------------------- |
| Backend    | `http://localhost:8000` |
| AI Service | `http://localhost:9000` |
| Frontend   | `http://localhost:3000` |

확인 순서:

1. Chrome에서 `http://localhost:3000`을 연다.
2. DevTools를 연다.
3. `Network > WS`로 이동한다.
4. `/ws/drains/status` 요청을 선택한다.
5. `Messages` 탭을 열어 둔다.
6. Swagger `http://localhost:8000/docs`에서 `POST /api/analysis/async-run`을 실행한다.

Request body:

```json
{
  "drainId": "DR-004"
}
```

기대 결과:

| 이벤트                   | 확인할 핵심 값                                               |
| ------------------------ | ------------------------------------------------------------ |
| `YOLO_RESULT_UPDATED`    | `payload.drainId`가 `DR-004`, YOLO 결과 ID와 막힘률 존재     |
| `XGBOOST_RESULT_UPDATED` | `payload.drainId`가 `DR-004`, 위험도와 위험 점수 존재        |
| `DRAIN_STATUS_UPDATED`   | `payload.drainId`가 `DR-004`, 최종 위험도/센서값/막힘률 존재 |

기록할 표:

| 항목                          | 결과 | 실제 값 또는 메모 |
| ----------------------------- | ---- | ----------------- |
| `/ws/drains/status` 연결      | 정상 | 이미지 참고       |
| `YOLO_RESULT_UPDATED` 수신    | 정상 | 이미지 참고       |
| `XGBOOST_RESULT_UPDATED` 수신 | 정상 | 이미지 참고       |
| `DRAIN_STATUS_UPDATED` 수신   | 정상 | 이미지 참고       |
| 이벤트 `payload.drainId`      | 정상 | 이미지 참고       |
| 대시보드 위험도/점수 반영     | 정상 | 이미지 참고       |
| 상세 화면 위험도/점수 반영    | 정상 | 이미지 참고       |

첨부 이미지
![통합테스트_수동테스트결과](/frontend/docs/images/통합테스트_수동테스트결과화면.jpg)

참고:

- 기대 payload 예시는 `docs/test/ai-front-back-integration/test-data.json`의 `expectedWebSocketMessages`를 참고한다.
- 테스트를 반복할 때마다 `yoloResultId`, `xgboostResultId`, timestamp는 바뀌는 것이 정상이다.
- `imageUrl`이 `ai-server://mock/4`로 표시되면 현재 AI Service 목업 이미지 정책상 정상이다.
- 이벤트가 오지 않으면 백엔드 로그의 callback 200 여부와 AI Service 로그의 callback delivery 성공 여부를 함께 확인한다.

## 10. 직접 AI Service 호출 시 주의점

AI Service에 직접 아래 endpoint를 호출하면 accepted response는 받을 수 있다.

```text
POST http://localhost:9000/ai/analysis/run
```

하지만 이 방식은 백엔드의 `AnalysisJob`을 먼저 만들지 않기 때문에, AI Service가 callback을 보낼 때 백엔드에서 `Analysis request not found` 404가 발생할 수 있다.

전체 통합 테스트는 반드시 백엔드의 아래 endpoint에서 시작해야 한다.

```text
POST http://localhost:8000/api/analysis/async-run
```

## 11. 남은 리스크

| 리스크                            | 설명                                                                | 대응                                                                   |
| --------------------------------- | ------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| WebSocket 메시지 자동 검증 미완료 | 연결은 확인했지만 메시지 본문 자동 수신은 보류됨                    | 브라우저 DevTools에서 수동 확인하거나 Playwright/WS 테스트를 후속 추가 |
| AI 이미지 URL                     | `ai-server://mock/4`는 브라우저 이미지로 직접 표시되지 않을 수 있음 | 현재는 fallback 표시가 정상이며, 실제 이미지 제공은 후속 과제          |
| 테스트 데이터 누적                | 반복 실행으로 YOLO/XGBoost 이력이 계속 증가함                       | 필요 시 테스트 전 DB 초기화 또는 별도 테스트 drain 사용                |

## 12. 최종 판단

AI Service 내부 테스트와 Backend-AI callback 저장, REST 조회, 프론트 경로 접근은 정상이다.

현재 기준에서 AI-프론트-백엔드 통합 흐름은 WebSocket 메시지 본문 자동 검증을 제외하고 통과로 판단한다.

## 13. 추천 커밋 메시지

제목:

```text
docs: AI 통합 테스트 결과 정리
```

내용:

```text
- AI Service pytest와 Backend-AI smoke test 결과를 기록한다.
- AI callback 저장과 최신 분석 조회 결과를 정리한다.
- WebSocket 자동 수신 보류와 남은 리스크를 문서화한다.
```


