# 프론트엔드-백엔드 통합 테스트 가이드라인

## 1. 문서 목적

| 항목        | 내용                                                                           |
| ----------- | ------------------------------------------------------------------------------ |
| 기준일      | 2026-06-18                                                                     |
| 대상 브랜치 | `test/front-back-first-merge-test` 또는 현재 작업 브랜치                       |
| 작업 범위   | SmartDrain backend와 frontend의 첫 통합 테스트                                 |
| 기준 명세   | `docs/11_API명세서.md`, `frontend/docs/api-spec/2026-06-18_mvp_api_spec_v1.md` |
| 테스트 목적 | API 명세서대로 데이터가 저장, 조회, 화면 표시되는지 확인하고 문제 항목을 기록  |

이 문서는 plan 문서 대신 통합 테스트 진행 순서를 남기기 위한 가이드이다. 테스트 중 문제가 발견되면 이 문서의 체크리스트와 이슈 기록 표에 바로 표시한다.

---

## 2. 테스트 전 확인

### 2.1 브랜치 확인

```powershell
git status --short --branch
```

확인 기준:

| 확인 항목      | 기대값                                           |
| -------------- | ------------------------------------------------ |
| 브랜치명       | `test/front-back-first-merge-test` 계열인지 확인 |
| 미커밋 변경    | 테스트 전 의도하지 않은 변경이 있는지 확인       |
| 문서 수정 범위 | `frontend/docs/` 내부 문서만 수정되는지 확인     |

현재 로컬에서 브랜치명이 `text/front-back-first-merge-test`처럼 보이면, 사용자가 의도한 `test/front-back-first-merge-test`와 다른 브랜치일 수 있으므로 테스트 시작 전에 팀 기준 브랜치명을 한 번 확인한다.

### 2.2 API 계약 핵심 기준

| 구분           | 기준                                               |
| -------------- | -------------------------------------------------- |
| REST base URL  | `http://localhost:8000`                            |
| Frontend env   | `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`   |
| WebSocket URL  | `ws://localhost:8000/ws/drains/status`             |
| 응답 wrapper   | 단건 `ApiResponse<T>`, 목록 `ApiListResponse<T>`   |
| 응답 필드명    | camelCase                                          |
| 위험도 코드    | `good`, `caution`, `danger`, `unknown`             |
| YOLO 상태 코드 | `clear`, `partially_blocked`, `blocked`, `unknown` |
| 막힘률         | `obstructionRatio` 0~1 ratio                       |
| 수위           | `waterLevelCm` cm                                  |
| 유속           | `flowVelocityMps` m/s                              |
| 시간           | ISO 8601 문자열, 가능하면 `+09:00` 포함            |

---

## 3. 로컬 실행 준비

### 3.1 Python 3.12 확인

백엔드는 Python 3.12 기준으로 테스트한다. 현재 PC의 기본 `python`이 3.14처럼 더 높은 버전으로 잡혀 있으면, `opencv-python`, `ultralytics`, `xgboost`, `psycopg[binary]` 같은 의존성에서 설치 또는 실행 문제가 날 수 있다.

Python 3.12 설치 후 PowerShell에서 버전을 확인한다.

```powershell
py --list
py -3.12 --version
```

확인 기준:

| 확인 항목        | 기대값                            |
| ---------------- | --------------------------------- |
| Python Launcher  | `py --list`에 `3.12` 표시         |
| Python 버전      | `Python 3.12.x`                   |
| 통합 테스트 기준 | backend venv는 Python 3.12로 생성 |

`py --list`에서 3.12가 보이지 않으면 Python 3.12 설치 옵션에서 Python Launcher 또는 PATH 등록이 빠졌을 수 있다. 이 경우 설치 파일을 다시 실행해 Python Launcher와 PATH 등록을 확인한다.

### 3.2 DB 실행

루트 경로에서 PostgreSQL 컨테이너를 실행한다.

```powershell
docker compose up -d db
```

확인 기준:

| 확인 항목 | 기대값                                                                                           |
| --------- | ------------------------------------------------------------------------------------------------ |
| 컨테이너  | `smartdrain-postgres` 실행 중                                                                    |
| DB URL    | `.env.example` 기준 `postgresql+psycopg://smartdrain:smartdrain123@localhost:5432/smartdrain_db` |

루트 `.env`의 `CORS_ORIGINS`는 pydantic-settings가 리스트로 읽을 수 있도록 JSON 배열 형식으로 둔다.

```env
CORS_ORIGINS=["http://localhost:3000"]
```

### 3.3 백엔드 실행

루트 경로에서 `backend`로 이동한 뒤 진행한다.

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\activate
python --version
pip install -r requirements.txt
copy .env.example .env
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

`python --version`이 `Python 3.12.x`가 아니면 venv를 잘못 만든 상태이므로, 통합 테스트를 시작하지 않고 Python 3.12 venv를 다시 만든다.

백엔드 확인:

| 확인 항목    | URL                          | 기대값                             |
| ------------ | ---------------------------- | ---------------------------------- |
| Health check | `http://localhost:8000/`     | `success: true`, `data.status: ok` |
| Swagger      | `http://localhost:8000/docs` | API 문서 표시                      |

### 3.4 프론트엔드 실행

`frontend/.env.local`에 API base URL을 설정한다.

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

프론트엔드 실행:

```powershell
cd frontend
pnpm install
pnpm dev
```

확인 기준:

| 확인 항목     | 기대값                                                                 |
| ------------- | ---------------------------------------------------------------------- |
| 개발 서버     | `http://localhost:3000` 접속 가능                                      |
| 대시보드      | API 호출 성공 시 실제 데이터 표시                                      |
| fallback 구분 | API base URL이 없거나 호출 실패 시 placeholder 또는 mock fallback 표시 |

---

## 4. 테스트 데이터 생성 순서

이 섹션은 FastAPI Swagger 기준으로 진행한다. PowerShell 명령어는 사용하지 않는다.

Swagger 접속 URL:

```text
http://localhost:8000/docs
```

Swagger에서 API를 실행하는 공통 순서:

1. 테스트할 API 줄을 펼친다.
2. `Try it out` 버튼을 누른다.
3. Request body 또는 path/query 값을 입력한다.
4. `Execute` 버튼을 누른다.
5. `Server response`의 status code와 response body를 확인한다.

테스트 데이터는 아래 순서로 만든다.

```text
POST /api/drains
→ POST /api/sensor-data
→ POST /api/analysis/yolo
→ POST /api/analysis/xgboost
```

이 순서의 의미:

| 순서 | API                          | 하는 일                                             |
| ---- | ---------------------------- | --------------------------------------------------- |
| 1    | `POST /api/drains`           | 테스트용 빗물받이를 만든다                          |
| 2    | `POST /api/sensor-data`      | 만든 빗물받이에 수위/유속 데이터를 넣는다           |
| 3    | `POST /api/analysis/yolo`    | 만든 빗물받이에 CCTV 막힘 분석 결과를 넣는다        |
| 4    | `POST /api/analysis/xgboost` | 센서 데이터와 YOLO 결과를 묶어 최종 위험도를 만든다 |

주의:

예시의 `drainId`, `sensorDataId`, `yoloResultId`는 모두 `1`로 되어 있다. 이미 테스트 데이터를 여러 번 만들었다면 실제 숫자 ID가 `2`, `3`처럼 달라질 수 있다. 이 경우 각 POST 응답 body에 나온 `data.id` 값을 다음 요청에 사용한다.

### 4.1 테스트 빗물받이 생성

Swagger에서 `POST /api/drains`를 펼친다.

Request body:

```json
{
  "drainCode": "DR-INT-001",
  "name": "통합 테스트 빗물받이",
  "address": "서울시 광진구 통합테스트로 1",
  "latitude": 37.5472,
  "longitude": 127.0743,
  "status": "good"
}
```

확인 기준:

| 필드             | 기대값       |
| ---------------- | ------------ |
| `success`        | `true`       |
| `data.id`        | `DR-INT-001` |
| `data.riskLevel` | `good`       |
| `timestamp`      | 존재         |

다음 단계에서 사용할 값:

| 값        | 설명                                                                                              |
| --------- | ------------------------------------------------------------------------------------------------- |
| `drainId` | 기본 예시는 `1` 사용. 이미 데이터가 있으면 응답의 숫자 ID 또는 Swagger 응답을 보고 실제 값을 사용 |

### 4.2 센서 데이터 저장

Swagger에서 `POST /api/sensor-data`를 펼친다.

Request body:

```json
{
  "drainId": 1,
  "waterLevelCm": 85,
  "flowVelocityMps": 0.05
}
```

확인 기준:

| 필드                   | 기대값          |
| ---------------------- | --------------- |
| `success`              | `true`          |
| `data.waterLevelCm`    | `85`            |
| `data.flowVelocityMps` | `0.05`          |
| `data.measuredAt`      | ISO 8601 문자열 |

다음 단계에서 사용할 값:

| 값             | 설명                  |
| -------------- | --------------------- |
| `sensorDataId` | 응답 body의 `data.id` |

### 4.3 YOLO 결과 저장

Swagger에서 `POST /api/analysis/yolo`를 펼친다.

Request body:

```json
{
  "drainId": 1,
  "imageUrl": "/static/samples/drain_int_001.jpg",
  "obstructionRatio": 0.88,
  "confidenceScore": 0.94,
  "yoloStatus": "blocked"
}
```

확인 기준:

| 필드                    | 기대값    |
| ----------------------- | --------- |
| `success`               | `true`    |
| `data.obstructionRatio` | 0~1 범위  |
| `data.confidenceScore`  | 0~1 범위  |
| `data.yoloStatus`       | `blocked` |

다음 단계에서 사용할 값:

| 값             | 설명                  |
| -------------- | --------------------- |
| `yoloResultId` | 응답 body의 `data.id` |

### 4.4 XGBoost 위험도 판단 실행

Swagger에서 `POST /api/analysis/xgboost`를 펼친다.

Request body:

```json
{
  "drainId": 1,
  "sensorDataId": 1,
  "yoloResultId": 1
}
```

확인 기준:

| 필드                 | 기대값                                                           |
| -------------------- | ---------------------------------------------------------------- |
| `success`            | `true`                                                           |
| `data.riskLevel`     | `good`, `caution`, `danger`, `unknown` 중 하나                   |
| `data.riskScore`     | 0~1 범위                                                         |
| `data.finalDecision` | 화면에 표시 가능한 문장                                          |
| WebSocket            | 연결 중인 클라이언트가 있으면 `DRAIN_STATUS_UPDATED` 이벤트 수신 |

---

## 5. REST API 조회 테스트

이 섹션도 Swagger 기준으로 진행한다. 4번에서 만든 테스트 데이터가 조회 API로 잘 나오는지 확인하는 단계이다.

Swagger에서 GET API를 실행하는 공통 순서:

1. 테스트할 `GET` API 줄을 펼친다.
2. `Try it out` 버튼을 누른다.
3. `{drain_id}`가 있으면 `DR-INT-001`을 입력한다.
4. query parameter가 있으면 문서에 적힌 값을 입력한다.
5. `Execute` 버튼을 누른다.
6. `Response body`의 필드가 확인 기준과 맞는지 본다.

### 5.1 빗물받이 목록

Swagger에서 `GET /api/drains`를 실행한다.

입력값 없음.

확인 기준:

| 확인 항목   | 기대값                                                                                                                                                           |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| wrapper     | `success`, `data.items`, `data.totalCount`, `timestamp` 존재                                                                                                     |
| 목록 item   | `id`, `roadAddress`, `latitude`, `longitude`, `riskLevel`, `riskScore`, `obstructionRatio`, `waterLevelCm`, `flowVelocityMps`, `finalDecision`, `updatedAt` 존재 |
| 프론트 영향 | 지도 마커, 위험 시설 목록, 선택 패널에 필요한 데이터가 모두 있음                                                                                                 |

### 5.2 빗물받이 상세

Swagger에서 `GET /api/drains/{drain_id}`를 실행한다.

입력값:

| 항목       | 값           |
| ---------- | ------------ |
| `drain_id` | `DR-INT-001` |

확인 기준:

| 확인 항목   | 기대값                                                                                          |
| ----------- | ----------------------------------------------------------------------------------------------- |
| 기본 필드   | 목록 item 필드와 동일                                                                           |
| 상세 필드   | `imageUrl`, `sensorSummary`, `sensorHistory`, `yoloResult`, `xgboostResult`, `riskHistory` 확인 |
| 프론트 영향 | `/drains/DR-INT-001` 상세 화면을 그릴 수 있음                                                   |

### 5.3 센서 이력

Swagger에서 `GET /api/drains/{drain_id}/sensors`를 실행한다.

입력값:

| 항목       | 값           |
| ---------- | ------------ |
| `drain_id` | `DR-INT-001` |
| `range`    | `24h`        |
| `limit`    | `48`         |

확인 기준:

| 확인 항목   | 기대값                                          |
| ----------- | ----------------------------------------------- |
| wrapper     | 목록 wrapper 구조                               |
| item        | `measuredAt`, `waterLevelCm`, `flowVelocityMps` |
| 프론트 영향 | 수위/유속 차트 데이터로 사용 가능               |

### 5.4 위험 이력

Swagger에서 `GET /api/drains/{drain_id}/risk-history`를 실행한다.

입력값:

| 항목       | 값           |
| ---------- | ------------ |
| `drain_id` | `DR-INT-001` |
| `days`     | `7`          |
| `limit`    | `10`         |

확인 기준:

| 확인 항목   | 기대값                                |
| ----------- | ------------------------------------- |
| wrapper     | 목록 wrapper 구조                     |
| item        | `changedAt`, `riskLevel`, `riskScore` |
| 프론트 영향 | 상세 화면 위험 이력 표시 가능         |

### 5.5 최신 분석 결과

Swagger에서 `GET /api/drains/{drain_id}/analysis/latest`를 실행한다.

입력값:

| 항목       | 값           |
| ---------- | ------------ |
| `drain_id` | `DR-INT-001` |

확인 기준:

| 확인 항목       | 기대값           |
| --------------- | ---------------- |
| `sensorSummary` | 최신 수위/유속   |
| `yoloResult`    | 최신 막힘 분석   |
| `xgboostResult` | 최신 위험도 판단 |
| `updatedAt`     | 최신 갱신 시각   |

### 5.6 대시보드 요약

Swagger에서 `GET /api/dashboard/summary`를 실행한다.

입력값 없음.

확인 기준:

| 확인 항목   | 기대값                                                                   |
| ----------- | ------------------------------------------------------------------------ |
| 개수 필드   | `totalCount`, `goodCount`, `cautionCount`, `dangerCount`, `unknownCount` |
| 합계        | 상태별 count 합이 `totalCount`와 일치                                    |
| 프론트 영향 | 대시보드 요약 카드에 표시 가능                                           |

---

## 6. WebSocket 테스트

백엔드 WebSocket endpoint는 `ws://localhost:8000/ws/drains/status`이다.

브라우저 개발자 도구 Console에서 다음을 실행한다.

```js
const socket = new WebSocket("ws://localhost:8000/ws/drains/status");
socket.onopen = () => console.log("ws connected");
socket.onmessage = (event) => console.log("ws message", JSON.parse(event.data));
socket.onerror = (event) => console.log("ws error", event);
socket.onclose = () => console.log("ws closed");
```

연결 후 `POST /api/analysis/xgboost`를 다시 실행한다.

확인 기준:

| 확인 항목   | 기대값                                                                                                                        |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------- |
| 연결        | `ws connected` 로그 표시                                                                                                      |
| 이벤트 타입 | `DRAIN_STATUS_UPDATED`                                                                                                        |
| payload     | `drainId`, `riskLevel`, `riskScore`, `waterLevelCm`, `flowVelocityMps`, `obstructionRatio`, `finalDecision`, `updatedAt` 포함 |
| 식별자      | `payload.drainId`가 REST 응답의 `data.id`와 같은 기준                                                                         |

현재 프론트 화면에서 WebSocket 자동 갱신 코드가 아직 연결되지 않았다면, 백엔드 이벤트 수신까지만 통과로 기록하고 화면 자동 갱신은 후속 이슈로 남긴다.

---

## 7. 프론트 화면 확인

### 7.1 대시보드

접속 URL:

```text
http://localhost:3000
```

확인 기준:

| 영역           | 기대 동작                                                                           |
| -------------- | ----------------------------------------------------------------------------------- |
| 요약 카드      | `GET /api/dashboard/summary` 데이터 반영                                            |
| 지도 영역      | `GET /api/drains` item 기준 마커 또는 시설 상태 표시                                |
| 위험 시설 목록 | 위험도 우선순위대로 정렬                                                            |
| 선택 패널      | 선택한 시설의 수위, 유속, 막힘률, 최종 판단 표시                                    |
| fallback       | API 실패 시 실제 데이터처럼 보이는 mock row가 아니라 placeholder/fallback 상태 표시 |

### 7.2 상세 페이지

접속 URL:

```text
http://localhost:3000/drains/DR-INT-001
```

확인 기준:

| 영역      | 기대 동작                                                            |
| --------- | -------------------------------------------------------------------- |
| 기본 정보 | 주소, 상태, 최근 업데이트 표시                                       |
| 센서 차트 | 센서 이력 API 결과로 수위/유속 표시                                  |
| CCTV/YOLO | `imageUrl`, `obstructionRatio`, `confidenceScore`, `yoloStatus` 표시 |
| XGBoost   | `riskScore`, `riskLevel`, `finalDecision` 표시                       |
| 위험 이력 | `riskHistory` 기준 최근 변화 표시                                    |
| 오류 상태 | 없는 ID 접근 시 상세 없음 또는 연결 대기 상태로 표시                 |

---

## 8. 에러 응답 테스트

### 8.1 존재하지 않는 빗물받이

Swagger에서 `GET /api/drains/{drain_id}`를 실행한다.

입력값:

| 항목       | 값             |
| ---------- | -------------- |
| `drain_id` | `DR-NOT-FOUND` |

확인 기준:

| 필드            | 기대값            |
| --------------- | ----------------- |
| `success`       | `false`           |
| `data`          | `null`            |
| `error.code`    | `DRAIN_NOT_FOUND` |
| `error.message` | 원인 확인 가능    |
| `timestamp`     | 존재              |

### 8.2 잘못된 요청값

예: 필수 필드가 빠진 POST 요청을 Swagger에서 실행한다.

확인 기준:

| 필드                  | 기대값                   |
| --------------------- | ------------------------ |
| HTTP status           | 422                      |
| `success`             | `false`                  |
| `error.code`          | `VALIDATION_ERROR`       |
| `error.detail.errors` | 검증 실패 위치 확인 가능 |

---

## 9. 최종 체크리스트

| 구분     | 체크 항목                                                          | 상태      | 비고 |
| -------- | ------------------------------------------------------------------ | --------- | ---- |
| 실행     | DB 컨테이너가 정상 실행된다                                        | 확인 필요 |      |
| 실행     | 백엔드 서버가 `localhost:8000`에서 실행된다                        | 확인 필요 |      |
| 실행     | 프론트 서버가 `localhost:3000`에서 실행된다                        | 확인 필요 |      |
| 환경변수 | `NEXT_PUBLIC_API_BASE_URL`이 설정되어 있다                         | 확인 필요 |      |
| REST     | `POST /api/drains`로 테스트 시설을 생성할 수 있다                  | 확인 필요 |      |
| REST     | `POST /api/sensor-data`로 센서 데이터를 저장할 수 있다             | 확인 필요 |      |
| REST     | `POST /api/analysis/yolo`로 YOLO 결과를 저장할 수 있다             | 확인 필요 |      |
| REST     | `POST /api/analysis/xgboost`로 위험도를 판단할 수 있다             | 확인 필요 |      |
| REST     | `GET /api/drains`가 목록 wrapper와 필수 필드를 반환한다            | 확인 필요 |      |
| REST     | `GET /api/drains/{id}`가 상세 화면 필드를 반환한다                 | 확인 필요 |      |
| REST     | `GET /api/drains/{id}/sensors`가 차트 데이터를 반환한다            | 확인 필요 |      |
| REST     | `GET /api/drains/{id}/risk-history`가 위험 이력을 반환한다         | 확인 필요 |      |
| REST     | `GET /api/drains/{id}/analysis/latest`가 최신 분석 결과를 반환한다 | 확인 필요 |      |
| REST     | `GET /api/dashboard/summary`가 요약 count를 반환한다               | 확인 필요 |      |
| WS       | `WS /ws/drains/status`가 연결된다                                  | 확인 필요 |      |
| WS       | XGBoost POST 후 `DRAIN_STATUS_UPDATED` 이벤트를 수신한다           | 확인 필요 |      |
| Frontend | 대시보드가 API 데이터를 표시한다                                   | 확인 필요 |      |
| Frontend | 상세 페이지가 API 데이터를 표시한다                                | 확인 필요 |      |
| Frontend | API 실패 시 fallback 상태가 명확히 보인다                          | 확인 필요 |      |
| Error    | 없는 ID 요청 시 공통 에러 wrapper를 반환한다                       | 확인 필요 |      |
| Error    | 검증 실패 시 `VALIDATION_ERROR`를 반환한다                         | 확인 필요 |      |

상태 값은 `통과`, `실패`, `보류`, `해당 없음` 중 하나로 기록한다.

---

## 10. 이슈 기록 양식

| 번호 | 발견 위치 | 재현 순서 | 기대 결과 | 실제 결과 | 심각도 | 담당 | 상태 |
| ---- | --------- | --------- | --------- | --------- | ------ | ---- | ---- |
| 1    |           |           |           |           |        |      |      |

심각도 기준:

| 심각도 | 기준                                                                |
| ------ | ------------------------------------------------------------------- |
| High   | 서버 실행 불가, 주요 API 500, 화면 진입 불가, 데이터 저장/조회 불가 |
| Medium | 특정 필드 누락, 화면 일부 깨짐, count 불일치, WebSocket 이벤트 누락 |
| Low    | 문구, 표시 형식, 정렬, fallback 배지 등 사용성 문제                 |

---

## 11. 통합 테스트 완료 기준

아래 조건을 만족하면 첫 통합 테스트를 완료로 본다.

1. 테스트 데이터 생성 API 4개가 모두 성공한다.
2. 프론트 연동용 GET API 6개가 공통 wrapper와 camelCase 필드를 반환한다.
3. 위험도, 막힘률, 수위, 유속, 시간 단위가 명세와 맞는다.
4. 대시보드와 상세 페이지가 실제 API 데이터를 표시한다.
5. API 실패나 없는 데이터 상태가 화면에서 mock 실제값처럼 보이지 않는다.
6. WebSocket은 최소한 백엔드 이벤트 수신까지 확인한다.
7. 실패 항목은 이슈 기록 표에 재현 순서와 기대/실제 결과를 남긴다.

---

## 12. 테스트 후 정리

테스트가 끝나면 다음 내용을 PR 문서 또는 작업 기록에 옮긴다.

| 항목             | 기록 내용                                                                |
| ---------------- | ------------------------------------------------------------------------ |
| 테스트 환경      | 브랜치, OS, Node/Python 버전, DB 실행 방식                               |
| 실행 명령        | DB, backend, frontend 실행 명령                                          |
| 통과 항목        | 최종 체크리스트에서 `통과` 처리한 항목                                   |
| 실패 항목        | 이슈 기록 표 전체                                                        |
| API 변경 필요    | 명세와 실제 응답이 달라 수정해야 하는 endpoint/DTO                       |
| 프론트 변경 필요 | adapter, 화면, fallback, WebSocket 연결 등 수정 필요 항목                |
| 백엔드 변경 필요 | schema, router, service, error handler, WebSocket manager 수정 필요 항목 |

추천 커밋 메시지:

```text
docs: 프론트-백엔드 통합 테스트 가이드 추가
```

```text
- SmartDrain MVP API 명세 기준 통합 테스트 순서를 정리한다.
- REST, WebSocket, 프론트 화면 확인 기준과 이슈 기록 양식을 추가한다.
- 첫 병합 테스트에서 확인할 환경 설정과 완료 기준을 문서화한다.
```
