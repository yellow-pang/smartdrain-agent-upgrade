# 07 WebSocket 이후 프론트-백엔드 통합 테스트 계획

## 1. 작업 개요

| 항목 | 내용 |
|---|---|
| 브랜치 | `test/frontend-backend-integration-after-ws` |
| 작업 범위 | `/frontend/docs` 내부 통합 테스트 문서와 테스트 자료 추가 |
| 기준 문서 | `frontend/docs/front-back-integration-test-guideline.md`, `frontend/docs/steps/step-08-realtime-analysis-contract-detail-ui.md`, `frontend/docs/contract/backend-contract-doc.md` |
| 목적 | step-08 이후 프론트가 준비한 REST/WebSocket 계약을 실제 백엔드와 연결해 사용자가 직접 검증할 수 있게 한다. |

이번 작업은 코드 수정이 아니라 통합 테스트 실행 준비 작업이다. 사용자가 직접 Swagger, 브라우저, DevTools를 사용해 테스트하고 결과를 체크할 수 있도록 계획, 체크리스트, 예시 데이터를 분리해 둔다.

## 2. 현재 단계 판단

| 구분 | 현재 상태 | 이번 테스트에서 확인할 것 |
|---|---|---|
| REST 목록/상세 | 기존 1차 통합 테스트에서 주요 API 연동 확인됨 | step-08 이후 추가된 상세 화면 데이터가 실제 응답과 맞는지 재확인 |
| WebSocket | `DRAIN_STATUS_UPDATED` 수신 흐름 확인 기록 있음 | 신규 `YOLO_RESULT_UPDATED`, `XGBOOST_RESULT_UPDATED` 이벤트까지 확인 |
| 상세 화면 | YOLO/XGBoost 탭, 분석 요약, CCTV 이력 UI 준비됨 | 실제 history 응답과 이벤트로 화면이 갱신되는지 확인 |
| history API | 프론트는 `GET /api/drains/{drain_id}/analysis/history?limit=10` 우선 기준 | 백엔드 제공 여부, 응답 필드, fallback 동작 확인 |
| 테스트 데이터 | 기존 문서에 조각별 예시 존재 | 복사하기 쉬운 JSON 예시 파일로 정리 |

## 3. 확인한 문서

- `frontend/AGENTS.md`: 중간 이상 작업은 plan 작성, `/frontend` 내부 작업, 검증 기준과 한글 문서 작성 기준을 확인했다.
- `frontend/docs/convention/documentation-convention.md`: plan, step, PR 문서 작성 흐름과 한국어 문서화 기준을 확인했다.
- `frontend/docs/front-back-integration-test-guideline.md`: 첫 통합 테스트의 실행 환경, Swagger 테스트 순서, REST/WebSocket 확인 기준을 확인했다.
- `frontend/docs/steps/step-08-realtime-analysis-contract-detail-ui.md`: 상세 화면이 신규 이벤트와 분석 이력 API를 받을 준비가 되었음을 확인했다.
- `frontend/docs/contract/backend-contract-doc.md`: 백엔드에 기대하는 WebSocket payload와 분석 이력 REST 응답 구조를 확인했다.
- `frontend/package.json`: 검증 스크립트는 `pnpm lint`, `pnpm build`이며 문서 작업 자체에는 실행이 필수는 아니다.

## 4. 이번 작업 산출물

| 파일 | 목적 |
|---|---|
| `docs/plans/plan-07-front-back-integration-after-ws.md` | 현재 브랜치에서 진행할 통합 테스트 계획과 사용자 실행 가이드 |
| `docs/test/front-back-integration-after-ws-checklist.md` | 테스트 중 바로 체크할 수 있는 항목별 체크리스트 |
| `docs/test/front-back-integration-example-data.json` | 기존 seed에 없는 추가 케이스가 필요할 때 Swagger Request body에 복사할 테스트 예시 데이터 |

## 5. 기존 DB 입력 파일 점검 결과

백엔드에는 이미 통합 테스트용 seed 파일이 있다.

| 파일 | 역할 |
|---|---|
| `backend/app/seeds/seed_mock_data.py` | `DR-001`~`DR-005` 시설과 센서, YOLO, XGBoost 결과를 DB에 생성 |
| `backend/README.md` | seed 실행 방법과 확인할 API 목록 안내 |

기존 seed가 생성하는 대표 데이터:

| drain code | 상태 | 화면 테스트 용도 |
|---|---|---|
| `DR-001` | `good` | 정상 상태 표시 |
| `DR-003` | `caution` | 주의 상태 표시 |
| `DR-004` | `danger` | 위험 상태, 상세 화면, WebSocket 테스트 기준 |
| `DR-005` | `unknown` | 알 수 없음 상태 표시 |

따라서 DB에 넣을 데이터는 아래 우선순위로 사용한다.

1. 기본 통합 테스트는 기존 `backend/app/seeds/seed_mock_data.py`를 먼저 사용한다.
2. step-08 이후 WebSocket/history 추가 검증에서 더 많은 YOLO 이미지나 오류 케이스가 필요할 때만 `front-back-integration-example-data.json`를 Swagger에 복사해 추가 입력한다.
3. 기존 seed는 `/frontend` 밖 파일이므로 이 작업에서는 수정하지 않는다. seed 내용을 바꾸려면 별도 사용자 확인 후 백엔드 파일을 수정한다.

## 6. 테스트 전 준비

### 6.1 브랜치와 변경 상태 확인

루트 경로에서 확인한다.

```powershell
git status --short --branch
```

기대값:

| 항목 | 기대 결과 |
|---|---|
| 브랜치 | `test/frontend-backend-integration-after-ws` |
| 변경 파일 | 테스트 시작 전 의도하지 않은 코드 변경 없음 |
| 수정 범위 | 통합 테스트 중 기록은 `frontend/docs/test` 중심으로 남김 |

### 6.2 백엔드 실행 확인

루트 경로에서 DB와 백엔드를 실행한다. 이미 실행 중이면 상태만 확인한다.

```powershell
docker compose up -d db
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

확인 URL:

| URL | 기대 결과 |
|---|---|
| `http://localhost:8000/` | `success: true`, `data.status: ok` |
| `http://localhost:8000/docs` | Swagger 화면 표시 |

주의:

- Python은 3.12 기준으로 맞춘다.
- 루트 `.env`의 `CORS_ORIGINS`는 `["http://localhost:3000"]` 형태로 둔다.

### 6.3 기존 seed 데이터 입력

기본 테스트 데이터는 백엔드 seed 스크립트로 넣는다.

```powershell
cd backend
python -m app.seeds.seed_mock_data
```

확인 기준:

| 항목 | 기대 결과 |
|---|---|
| 생성 로그 | `[SEED 완료]` 표시 |
| 중복 실행 | 이미 존재하는 `drain_code`는 건너뜀 |
| 대표 상세 URL | `http://localhost:3000/drains/DR-004` |

### 6.4 프론트엔드 실행 확인

`frontend/.env.local`에 아래 값을 둔다.

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

프론트엔드 실행:

```powershell
cd frontend
pnpm install
pnpm dev
```

확인 URL:

| URL | 기대 결과 |
|---|---|
| `http://localhost:3000` | 대시보드 표시 |
| `http://localhost:3000/drains/DR-INT-WS-001` | 테스트 데이터 생성 후 상세 화면 표시 |

## 7. 테스트 데이터 입력 가이드

기본 테스트는 기존 seed의 `DR-004`를 기준으로 진행한다.

추가 데이터가 필요할 때만 `frontend/docs/test/front-back-integration-example-data.json`를 열어 Swagger Request body에 복사한다.

권장 순서:

```text
POST /api/drains
POST /api/sensor-data
POST /api/analysis/yolo
POST /api/analysis/xgboost
GET /api/drains
GET /api/drains/{drain_id}
GET /api/drains/{drain_id}/analysis/latest
GET /api/drains/{drain_id}/analysis/history?limit=10
GET /api/dashboard/summary
```

중요:

- `POST /api/drains` 응답에서 후속 POST에 필요한 숫자 ID를 확인한다.
- 예시 데이터의 `drainId`, `sensorDataId`, `yoloResultId`는 반드시 Swagger 응답의 실제 값으로 바꿔 넣는다.
- 화면 URL에는 문자열 drain code인 `DR-INT-WS-001`을 사용한다.

## 8. 사용자 직접 테스트 상세 순서

### Step 1. 서버와 환경 변수 확인

1. 백엔드 `http://localhost:8000/`가 정상 응답하는지 확인한다.
2. Swagger `http://localhost:8000/docs`가 열리는지 확인한다.
3. 프론트 `http://localhost:3000`이 열리는지 확인한다.
4. DevTools Network에서 API 요청이 `http://localhost:8000`으로 나가는지 확인한다.

### Step 2. 기본 seed 데이터 확인

Swagger에서 `GET /api/drains` 또는 프론트 화면에서 `DR-004`가 있는지 확인한다.

기본 확인 URL:

```text
http://localhost:3000/drains/DR-004
```

확인 기준:

| 확인 항목 | 기대 결과 |
|---|---|
| `DR-004` | 위험 상태 데이터 존재 |
| 센서 데이터 | 수위와 유속 표시 |
| YOLO 결과 | 막힘률과 이미지 정보 표시 |
| XGBoost 결과 | 위험도와 최종 판단 표시 |

추가 시설이 필요할 때만 Swagger에서 `POST /api/drains`를 실행하고 `front-back-integration-example-data.json > createDrain`을 사용한다.

### Step 3. 센서 데이터 생성

Swagger에서 `POST /api/sensor-data`를 2회 이상 실행한다.

사용 데이터:

```text
sensorData.caution
sensorData.danger
```

확인 기준:

| 확인 항목 | 기대 결과 |
|---|---|
| `success` | `true` |
| `data.waterLevelCm` | 요청값과 동일 |
| `data.flowVelocityMps` | 요청값과 동일 |
| `data.id` | XGBoost 요청에 사용할 `sensorDataId` |

### Step 4. YOLO 결과 생성

Swagger에서 `POST /api/analysis/yolo`를 2회 이상 실행한다.

사용 데이터:

```text
yoloResults.partiallyBlocked
yoloResults.blocked
```

확인 기준:

| 확인 항목 | 기대 결과 |
|---|---|
| `data.imageUrl` | 요청한 경로 |
| `data.obstructionRatio` | 0~1 ratio |
| `data.confidenceScore` | 0~1 ratio |
| `data.yoloStatus` | `clear`, `partially_blocked`, `blocked`, `unknown` 중 하나 |
| `data.id` | XGBoost 요청에 사용할 `yoloResultId` |

### Step 5. XGBoost 결과 생성

Swagger에서 `POST /api/analysis/xgboost`를 실행한다.

사용 데이터:

```text
xgboostRequests.danger
```

주의:

- `sensorDataId`와 `yoloResultId`는 Step 3, Step 4의 실제 응답 ID로 교체한다.
- 이 요청 직후 WebSocket 이벤트가 발생하는지 확인한다.

확인 기준:

| 확인 항목 | 기대 결과 |
|---|---|
| `success` | `true` |
| `data.riskLevel` | `good`, `caution`, `danger`, `unknown` 중 하나 |
| `data.riskScore` | 0~1 범위 |
| `data.finalDecision` | 화면에 표시 가능한 문장 |

### Step 6. WebSocket 이벤트 확인

Chrome DevTools에서 확인한다.

```text
F12 > Network > WS > /ws/drains/status > Messages
```

확인 이벤트:

| 이벤트 | 기대 payload |
|---|---|
| `DRAIN_STATUS_UPDATED` | 최종 위험도, 수위, 유속, 막힘률, 최종 판단 |
| `YOLO_RESULT_UPDATED` | YOLO 이미지, 막힘률, confidence score, 분석 시각 |
| `XGBOOST_RESULT_UPDATED` | 위험도, 위험 점수, 참조 sensor/yolo/xgboost ID |

백엔드가 아직 신규 이벤트 2개를 발행하지 않으면 다음처럼 기록한다.

```text
YOLO_RESULT_UPDATED: 보류 - 백엔드 이벤트 미발행
XGBOOST_RESULT_UPDATED: 보류 - 백엔드 이벤트 미발행
```

### Step 7. 대시보드 화면 확인

URL:

```text
http://localhost:3000
```

확인 기준:

| 영역 | 기대 결과 |
|---|---|
| 요약 카드 | `GET /api/dashboard/summary` count 반영 |
| 지도 | `DR-INT-WS-001` 위치 또는 상태 반영 |
| 위험 시설 목록 | 위험도와 점수 기준 표시 |
| 선택 패널 | 수위, 유속, 막힘률, 최종 판단 표시 |
| 실시간 상태 | WebSocket 연결 상태 표시 |

### Step 8. 상세 화면 확인

URL:

```text
http://localhost:3000/drains/DR-INT-WS-001
```

확인 기준:

| 영역 | 기대 결과 |
|---|---|
| 상단 요약 | 위험도, 위험 점수, 수위, 유속, 막힘률 표시 |
| CCTV | 최신 `imageUrl` 표시, 잘못된 이미지면 fallback 표시 |
| YOLO 탭 | obstructionRatio, confidenceScore, yoloStatus 표시 |
| XGBoost 탭 | riskScore, riskLevel, finalDecision, 참조 ID 표시 |
| 이력 탭 | history API가 있으면 최근 YOLO/XGBoost 이력 표시 |
| WebSocket 반영 | 같은 drainId 이벤트만 상세 화면에 반영 |

### Step 9. 새로고침 유지 확인

대시보드와 상세 화면을 새로고침한다.

확인 기준:

| 확인 항목 | 기대 결과 |
|---|---|
| 대시보드 | WebSocket으로 갱신된 값이 REST 조회에서도 유지 |
| 상세 화면 | 최신 위험도와 AI 분석 정보 유지 |
| 이력 | history API가 있으면 최근 이력 유지 |

### Step 10. 오류와 fallback 확인

확인할 항목:

| 시나리오 | 기대 결과 |
|---|---|
| 없는 drain 접근 | 화면이 깨지지 않고 없음/오류 상태 표시 |
| 잘못된 이미지 경로 | CCTV 영역이 깨지지 않고 fallback 표시 |
| 백엔드 중지 | API 실패 또는 WebSocket error/reconnecting 상태 표시 |
| history API 미제공 | 상세 화면은 유지되고 최신 분석 정보만 표시 |

## 9. 체크 기록 위치

테스트 중 결과는 아래 문서에 기록한다.

```text
frontend/docs/test/front-back-integration-after-ws-checklist.md
```

상태 값은 아래 중 하나로 통일한다.

| 상태 | 의미 |
|---|---|
| `통과` | 기대 결과와 실제 결과가 일치 |
| `실패` | 재현 가능한 오류가 있음 |
| `보류` | 백엔드 미구현, 환경 미준비 등으로 확인하지 못함 |
| `해당 없음` | 현재 테스트 범위에 포함하지 않음 |

## 10. 완료 기준

아래 조건을 만족하면 이번 통합 테스트를 완료로 본다.

1. Swagger로 테스트 시설, 센서, YOLO, XGBoost 데이터를 생성할 수 있다.
2. 대시보드가 REST 조회 데이터와 WebSocket 갱신 결과를 표시한다.
3. 상세 화면이 최신 YOLO/XGBoost 결과와 분석 요약을 표시한다.
4. history API가 제공되면 CCTV 이력과 AI 이력 탭이 실제 응답을 표시한다.
5. history API가 없더라도 상세 화면이 깨지지 않고 fallback 동작한다.
6. `DRAIN_STATUS_UPDATED`는 반드시 확인하고, 신규 YOLO/XGBoost 이벤트는 발행 여부를 명확히 기록한다.
7. 실패 항목은 체크리스트의 이슈 기록 표에 재현 순서와 기대/실제 결과를 남긴다.

## 11. 남은 리스크

| 리스크 | 설명 | 대응 |
|---|---|---|
| 백엔드 history endpoint 미제공 | 프론트는 통합 endpoint를 우선 호출한다. | 실패가 아니라 `보류`로 기록하고 최신 분석 fallback 확인 |
| WebSocket 신규 이벤트 미발행 | step-08 프론트는 받을 준비가 되었지만 백엔드 발행이 필요하다. | `DRAIN_STATUS_UPDATED`는 통과 여부 확인, 신규 이벤트는 백엔드 후속 이슈로 기록 |
| POST용 drainId 혼동 | 화면은 문자열 code, POST는 숫자 ID를 요구할 수 있다. | Swagger 응답의 실제 ID를 체크리스트에 기록 |
| 이미지 파일 미준비 | imageUrl이 실제 public 파일과 맞지 않으면 fallback이 나온다. | fallback 동작을 확인하거나 `frontend/public/test-snapshots`에 이미지 추가 |

## 12. 추천 커밋 메시지

제목:

```text
docs: WebSocket 이후 프론트-백엔드 통합 테스트 계획 추가
```

내용:

```text
- step-08 이후 REST와 WebSocket 통합 테스트 계획을 정리한다.
- 사용자가 직접 체크할 통합 테스트 체크리스트를 추가한다.
- Swagger 입력용 예시 데이터를 JSON으로 분리한다.
```
