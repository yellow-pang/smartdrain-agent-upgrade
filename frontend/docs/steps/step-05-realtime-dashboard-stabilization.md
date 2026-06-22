# 05_realtime dashboard stabilization 작업 기록

## 1. 이번 단계의 핵심 판단

이번 단계는 “AI 분석 원천 데이터를 모두 보여주는 화면”을 만드는 작업이 아니라, MVP 발표와 대시보드 사용 흐름에서 관리자가 바로 판단할 수 있는 화면을 안정화하는 작업이다.

따라서 상세 화면과 대시보드는 아래 기준으로 정리했다.

```text
관리자가 지금 봐야 하는 것
→ 어느 시설이 위험한가
→ 현재 위험도는 무엇인가
→ 막힘 정도, 수위, 유속은 어떤가
→ 최종 판단 문구는 무엇인가
→ WebSocket으로 최신 상태가 반영되는가
```

반대로 아래 항목은 1차 MVP 화면에서 직접 노출하지 않기로 했다.

```text
YOLO 원천 데이터
→ yoloStatus
→ confidenceScore
→ yoloResultId
→ analyzedAt

XGBoost 원천 데이터
→ xgboostId
→ yoloResultId
→ 모델 실행 단계의 상세 데이터

분석 실패 원천 데이터
→ stage
→ fallbackStatus
→ failure payload
```

이 값들은 AI/백엔드 검증에는 의미가 있지만, 현재 MVP 화면에서는 별도 카드로 노출하면 화면이 복잡해지고 레퍼런스 이미지의 첫 화면 구성과도 어긋난다.

## 2. 왜 YOLO 데이터를 직접 보여주지 않았는가

YOLO는 막힘 상태를 계산하는 중간 분석 단계다. 하지만 MVP 관리자 화면에서 중요한 것은 “YOLO가 어떤 class를 냈는지”보다 “현재 막힘 정도가 얼마나 높은지”다.

현재 백엔드와 REST/WebSocket 데이터에는 `obstructionRatio`가 있고, 이 값은 화면에서 `막힘 정도`로 표시할 수 있다.

그래서 이번 단계에서는 아래처럼 해석했다.

| 원천 데이터 | MVP 화면 표시 |
|---|---|
| `obstructionRatio` | 막힘 정도 |
| `imageUrl` | CCTV/스냅샷 이미지 |
| `confidenceScore` | 1차 화면에서는 직접 표시하지 않음 |
| `yoloStatus` | 1차 화면에서는 직접 표시하지 않음 |

즉, YOLO 분석 결과를 완전히 버린 것이 아니라, 관리자가 바로 이해할 수 있는 `막힘 정도`로만 화면에 반영한다.

## 3. 왜 XGBoost 데이터를 직접 보여주지 않았는가

XGBoost는 최종 위험도 판단 단계다. MVP 화면에서 중요한 것은 모델의 내부 실행 정보가 아니라 최종 위험도와 판단 문구다.

현재 백엔드 WebSocket 이벤트인 `DRAIN_STATUS_UPDATED`는 아래 값을 내려준다.

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

이 payload만으로도 MVP 화면에 필요한 최종 상태는 갱신할 수 있다.

| 원천 데이터 | MVP 화면 표시 |
|---|---|
| `riskLevel` | 상태 배지, 지도 마커 색상 |
| `riskScore` | 위험 점수 또는 내부 정렬 기준 |
| `finalDecision` | 판정 결과 |
| `updatedAt` | 최근 업데이트 |

그래서 별도의 `XGBoost 분석 결과` 카드는 제거하고, 현재 위험 상태와 시설 정보 안에서 필요한 값만 표시하는 방향으로 정리했다.

## 4. 왜 실패 데이터를 직접 보여주지 않았는가

현재 백엔드는 실패 이벤트를 WebSocket으로 발행하지 않는다.

현재 구현된 실시간 이벤트는 `DRAIN_STATUS_UPDATED`이며, `ANALYSIS_FAILED` 같은 이벤트는 아직 없다.

따라서 프론트가 실패 상세 화면을 먼저 만들면 다음 문제가 생긴다.

| 문제 | 설명 |
|---|---|
| 실제 이벤트가 없음 | 백엔드가 실패 payload를 보내지 않으므로 화면 상태를 실제로 갱신할 수 없음 |
| MVP 화면 복잡도 증가 | 관리자 화면에 아직 오지 않는 실패 상태 UI가 늘어남 |
| 테스트 기준 불명확 | 어떤 stage, 어떤 message를 받을지 확정되지 않음 |

그래서 이번 단계에서는 실패 데이터 자체를 화면에 노출하지 않고, WebSocket 연결 실패나 REST API 오류처럼 실제 프론트에서 확인 가능한 오류 상태만 유지한다.

## 5. 이번에 구현한 실시간 갱신 구조

이번 구현은 단일 WebSocket endpoint 기준이다.

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
→ ws://localhost:8000/ws/drains/status
→ DRAIN_STATUS_UPDATED 수신
→ payload.drainId 기준으로 기존 시설 데이터 병합
→ 지도, 위험 시설 목록, 선택 패널, 상세 화면 갱신
```

새로 추가한 WebSocket hook은 endpoint를 여러 개 만들지 않고, 메시지 내부 `type` 값으로 분기할 수 있게 만들었다.

현재는 `DRAIN_STATUS_UPDATED`만 처리한다.

나중에 백엔드가 같은 endpoint에서 `SENSOR_DATA_UPDATED`, `YOLO_RESULT_UPDATED`, `ANALYSIS_FAILED`를 추가하면 handler만 확장하면 된다.

## 6. 화면 기준 변경 내용

### 대시보드

대시보드는 WebSocket 이벤트 수신 시 해당 시설만 갱신한다.

갱신되는 값은 다음이다.

| 값 | 반영 위치 |
|---|---|
| `riskLevel` | 지도 마커 색상, 상태 배지, 위험 시설 목록 정렬 |
| `waterLevelCm` | 수위 표시 |
| `flowVelocityMps` | 유속 표시 |
| `obstructionRatio` | 막힘 정도 |
| `finalDecision` | 선택 시설 판단 문구 |
| `updatedAt` | 최근 업데이트 |

이벤트를 받을 때 전체 목록을 다시 조회하지 않는다. 기존 REST 데이터를 유지하고, `drainId`가 같은 시설만 부분 갱신한다.

### 상세 화면

상세 화면에서는 별도 `YOLO / XGBoost 분석 결과` 카드를 제거했다.

대신 아래 영역을 중심으로 유지한다.

| 영역 | 유지 이유 |
|---|---|
| CCTV/스냅샷 | 관리자가 현장 이미지를 확인해야 함 |
| 위치 지도 | 시설 위치 확인 |
| 센서 추세 차트 | 수위/유속 변화 확인 |
| 현재 위험 상태 | MVP의 핵심 판단 영역 |
| 시설 정보 | ID, 주소, 상태 확인 |
| 과거 위험 이력 | 반복 위험 여부 확인 |

상세 화면도 WebSocket 이벤트의 `drainId`가 현재 상세 시설과 같을 때만 갱신한다.

## 7. 변경 파일

| 파일 | 변경 내용 |
|---|---|
| `frontend/lib/websocket/drain-status-socket.ts` | WebSocket 연결 hook 추가 |
| `frontend/lib/api/types.ts` | `DRAIN_STATUS_UPDATED` payload nullable 대응 |
| `frontend/lib/api/adapters.ts` | WebSocket 이벤트를 UI 시설 데이터에 병합하는 helper 추가 |
| `frontend/app/page.tsx` | 대시보드에 WebSocket 연결 및 부분 갱신 적용 |
| `frontend/app/drains/[id]/page.tsx` | 상세 화면 WebSocket 갱신 적용, 별도 YOLO/XGBoost 카드 제거 |

## 8. 검증 결과

| 명령어 | 결과 | 비고 |
|---|---|---|
| `npm run lint` | 통과 | 기존 `fallback-image.tsx`의 `<img>` 경고 1개만 남음 |
| `npm run build` | 통과 | Next.js production build 성공 |

## 9. 이번 단계에서 남긴 리스크

| 리스크 | 이유 | 후속 방향 |
|---|---|---|
| 실제 WebSocket 수신 수동 테스트 미완료 | 백엔드 서버와 테스트 데이터가 떠 있어야 확인 가능 | 다음 브랜치에서 통합 테스트 진행 |
| `SENSOR_DATA_UPDATED` 없음 | 현재 백엔드가 센서 저장 시 broadcast하지 않음 | 필요 시 백엔드 이벤트 추가 요청 |
| `YOLO_RESULT_UPDATED` 없음 | 현재 백엔드가 YOLO 저장 시 broadcast하지 않음 | MVP 이후 단계별 분석 표시가 필요하면 추가 |
| `ANALYSIS_FAILED` 없음 | 현재 실패 이벤트 payload가 없음 | 실패 화면이 필요해지면 백엔드 명세 확정 |
| 상세 이미지 실시간 갱신 제한 | `DRAIN_STATUS_UPDATED`에 `imageUrl`이 없음 | 필요 시 최신 분석 REST 재조회 또는 payload 확장 |

## 10. 다음 브랜치 제안

다음 브랜치는 실제 WebSocket 수신과 화면 반영을 테스트하는 브랜치로 나누는 것이 좋다.

추천 브랜치명:

```text
test/realtime-websocket-verification
```

다음 브랜치에서 할 일:

1. 백엔드 서버와 프론트 dev 서버를 동시에 실행한다.
2. `ws://localhost:8000/ws/drains/status` 연결 여부를 브라우저 화면에서 확인한다.
3. Swagger 또는 백엔드 테스트 API로 `POST /api/analysis/xgboost`를 실행한다.
4. `DRAIN_STATUS_UPDATED` 이벤트가 프론트에 도착하는지 확인한다.
5. 지도 마커, 위험 시설 목록, 선택 패널, 상세 화면이 `drainId` 기준으로 갱신되는지 확인한다.
6. 연결 끊김, 백엔드 미실행, 잘못된 메시지 수신 시 화면이 멈추지 않는지 확인한다.
7. 여러 이미지 URL이 저장되고 상세 화면에서 이미지 표시가 가능한지도 확인한다.
8. 테스트 결과를 `frontend/docs/steps/step-06-realtime-websocket-verification.md`에 기록한다.

### 10.1 이미지 URL 테스트 지시사항

MVP에서는 이미지 파일 자체를 WebSocket이나 API body로 전송하지 않고, 이미지 URL 또는 경로만 저장한다.

다음 테스트 브랜치에서는 프론트엔드 정적 파일 폴더에 테스트 이미지를 미리 넣어두고, Swagger에서 YOLO 결과를 생성할 때 해당 경로를 `imageUrl`로 입력한다.

추천 테스트 이미지 위치:

```text
frontend/public/test-snapshots/
```

예시 파일:

```text
frontend/public/test-snapshots/drain-001-a.jpg
frontend/public/test-snapshots/drain-001-b.jpg
frontend/public/test-snapshots/drain-001-c.jpg
```

프론트에서 접근할 URL:

```text
/test-snapshots/drain-001-a.jpg
/test-snapshots/drain-001-b.jpg
/test-snapshots/drain-001-c.jpg
```

주의할 점:

| 항목 | 기준 |
|---|---|
| 파일 저장 위치 | `frontend/public/test-snapshots/` |
| API에 넣을 값 | `/test-snapshots/파일명.jpg` |
| WebSocket 전송 | 이미지 파일 전송 금지, URL만 사용 |
| git 관리 | 실제 테스트 이미지가 크면 커밋하지 말고 로컬 테스트용으로만 사용 |
| 화면 기대값 | 상세 화면 CCTV 영역에서 깨진 이미지 대신 해당 이미지가 표시되는지 확인 |

### 10.2 Swagger 테스트 데이터 양식

다음 브랜치에서 Swagger 테스트를 할 때 아래 순서로 데이터를 만든다.

#### 1. 빗물받이 생성

Endpoint:

```text
POST /api/drains
```

예시 body:

```json
{
  "drainCode": "DR-IMG-001",
  "address": "서울특별시 강남구 테스트로 101",
  "latitude": 37.4991,
  "longitude": 127.0328,
  "status": "unknown"
}
```

#### 2. 센서 데이터 생성

Endpoint:

```text
POST /api/sensor-data
```

예시 body:

```json
{
  "drainId": 1,
  "waterLevelCm": 85,
  "flowVelocityMps": 0.05,
  "qualityStatus": "valid",
  "measuredAt": "2026-06-19T10:00:00+09:00"
}
```

`drainId`는 실제 Swagger 응답의 DB 숫자 ID에 맞춰 바꾼다.

#### 3. YOLO 결과 여러 장 생성

Endpoint:

```text
POST /api/analysis/yolo
```

예시 body 1:

```json
{
  "drainId": 1,
  "imageUrl": "/test-snapshots/drain-001-a.jpg",
  "obstructionRatio": 0.35,
  "confidenceScore": 0.78,
  "yoloStatus": "partially_blocked",
  "capturedAt": "2026-06-19T10:00:00+09:00"
}
```

예시 body 2:

```json
{
  "drainId": 1,
  "imageUrl": "/test-snapshots/drain-001-b.jpg",
  "obstructionRatio": 0.72,
  "confidenceScore": 0.86,
  "yoloStatus": "blocked",
  "capturedAt": "2026-06-19T10:05:00+09:00"
}
```

예시 body 3:

```json
{
  "drainId": 1,
  "imageUrl": "/test-snapshots/drain-001-c.jpg",
  "obstructionRatio": 0.18,
  "confidenceScore": 0.81,
  "yoloStatus": "clear",
  "capturedAt": "2026-06-19T10:10:00+09:00"
}
```

확인할 것:

| 확인 항목 | 기대 결과 |
|---|---|
| 여러 YOLO 결과 저장 | Swagger 응답이 모두 성공 |
| 최신 이미지 기준 | 상세 화면이 최신 `capturedAt` 또는 최신 분석 기준 이미지를 표시 |
| 깨진 이미지 fallback | 잘못된 URL일 때 placeholder 표시 |

#### 4. XGBoost 결과 생성 및 WebSocket 이벤트 확인

Endpoint:

```text
POST /api/analysis/xgboost
```

예시 body:

```json
{
  "drainId": 1,
  "sensorDataId": 1,
  "yoloResultId": 2
}
```

확인할 것:

| 확인 항목 | 기대 결과 |
|---|---|
| WebSocket 이벤트 | `DRAIN_STATUS_UPDATED` 수신 |
| 대시보드 목록 | 위험도순 재정렬 |
| 지도 마커 | 위험도 색상 변경 |
| 상세 화면 | 현재 위험 상태 값 갱신 |
| 이미지 | REST 최신 데이터 기준 이미지 표시 |

### 10.3 다음 plans 문서에 넣을 테스트 진행 양식

다음 plan 문서를 만들 때 아래 양식을 그대로 사용하면 된다.

```markdown
# 05_realtime websocket verification 계획

## 1. 작업 개요

| 항목 | 내용 |
|---|---|
| 브랜치 | `test/realtime-websocket-verification` |
| 작업 범위 | `/frontend` 내부 문서 및 필요한 테스트 보조 파일 |
| 핵심 목적 | 실제 백엔드 WebSocket 수신과 화면 갱신 확인 |
| 추가 확인 | 여러 이미지 URL 저장 및 상세 화면 이미지 표시 |

## 2. 테스트 준비

| 준비 항목 | 내용 |
|---|---|
| Backend | `http://localhost:8000` |
| Frontend | `http://localhost:3000` |
| WebSocket | `ws://localhost:8000/ws/drains/status` |
| 이미지 폴더 | `frontend/public/test-snapshots/` |
| 이미지 URL | `/test-snapshots/*.jpg` |

## 3. Swagger 데이터 생성 순서

1. `POST /api/drains`
2. `POST /api/sensor-data`
3. `POST /api/analysis/yolo` 여러 번 실행
4. `POST /api/analysis/xgboost`
5. 프론트 화면 갱신 확인

## 4. 확인 항목

| 구분 | 확인 내용 | 결과 |
|---|---|---|
| WebSocket 연결 | 연결 상태가 `실시간 연결됨`으로 바뀌는가 |  |
| 이벤트 수신 | XGBoost 생성 후 `DRAIN_STATUS_UPDATED`가 수신되는가 |  |
| 목록 정렬 | 위험도순 목록이 자동 재정렬되는가 |  |
| 지도 | 마커 색상이 변경되는가 |  |
| 상세 화면 | 현재 위험 상태가 갱신되는가 |  |
| 이미지 | `/test-snapshots/...jpg` 이미지가 표시되는가 |  |
| fallback | 잘못된 이미지 URL일 때 placeholder가 표시되는가 |  |

## 5. 남은 이슈 기록

| 이슈 | 재현 순서 | 기대 결과 | 실제 결과 | 후속 조치 |
|---|---|---|---|---|
|  |  |  |  |  |
```

다음 브랜치에서 사용할 프롬프트:

```text
SmartDrain frontend의 실시간 WebSocket 수신 기능을 테스트하려고 합니다.

현재 브랜치에서는 /ws/drains/status 단일 endpoint에 연결하고,
DRAIN_STATUS_UPDATED 이벤트를 수신해 대시보드와 상세 화면을 drainId 기준으로 부분 갱신하도록 구현했습니다.

다음 브랜치명은 test/realtime-websocket-verification 입니다.

아래 기준으로 실제 통합 테스트를 진행해주세요.

1. frontend/AGENTS.md를 먼저 읽고 규칙을 지켜주세요.
2. /frontend 내부만 수정 가능합니다.
3. 백엔드 코드는 수정하지 말고, 필요한 백엔드 변경사항은 보고만 해주세요.
4. backend 서버와 frontend dev 서버 실행 상태를 확인해주세요.
5. WebSocket endpoint는 ws://localhost:8000/ws/drains/status 입니다.
6. 테스트 이벤트는 백엔드의 POST /api/analysis/xgboost 실행 후 발생하는 DRAIN_STATUS_UPDATED를 기준으로 확인해주세요.
7. 이벤트 수신 시 대시보드 지도, 위험 시설 목록, 선택 시설 패널, 상세 화면이 갱신되는지 확인해주세요.
8. WebSocket 연결 상태가 waiting, connected, reconnecting, error로 표시되는지 확인해주세요.
9. frontend/public/test-snapshots/ 폴더에 테스트 이미지를 두고 Swagger의 YOLO imageUrl에 /test-snapshots/파일명.jpg 형식으로 입력해 이미지 표시도 확인해주세요.
10. 여러 YOLO 결과를 생성했을 때 최신 이미지 또는 백엔드가 내려주는 imageUrl 기준으로 상세 화면이 어떻게 표시되는지 기록해주세요.
11. 테스트 중 발견한 문제는 frontend/docs/steps/step-06-realtime-websocket-verification.md에 기록해주세요.
12. 가능하면 npm run lint와 npm run build를 실행하고 결과를 기록해주세요.

최종 산출물:
- WebSocket 연결 확인 결과
- DRAIN_STATUS_UPDATED 수신 여부
- 화면 갱신 성공/실패 여부
- 여러 이미지 URL 저장 및 표시 확인 결과
- 남은 문제와 백엔드 확인 필요 항목
- 추천 커밋 메시지
```

## 11. 이번 단계 커밋 메시지

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
