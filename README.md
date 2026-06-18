# SmartDrain Flood Monitoring Backend

FastAPI 기반 지능형 도시 침수 관리 및 모니터링 MVP 백엔드입니다. 빗물받이/하수구 위치와 상태, 수위/유속 센서 데이터, YOLO 이미지 분석 결과, 규칙 기반 XGBoost 대체 위험도 판단 결과를 저장하고 조회합니다.

## Folder Structure

```text
backend/
  alembic/
  app/
    ai/
    core/
    models/
    routers/
    schemas/
    services/
    websocket/
    main.py
docker-compose.yml
requirements.txt
.env.example
```

## Local Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
cd backend
uvicorn app.main:app --reload
```

API 문서는 서버 실행 후 `http://localhost:8000/docs`에서 확인할 수 있습니다.

## PostgreSQL With Docker

```bash
docker compose up -d db
```

기본 PostgreSQL 연결 정보:

- container name: `smartdrain-postgres`
- user: `smartdrain`
- password: `smartdrain123`
- database: `smartdrain_db`
- URL: `postgresql+psycopg://smartdrain:smartdrain123@localhost:5432/smartdrain_db`

## .env Example

```env
PROJECT_NAME=Flood Monitoring Backend
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/flood_db
CORS_ORIGINS=http://localhost:3000
```

## Alembic Commands

```bash
alembic revision --autogenerate -m "create initial tables"
alembic upgrade head
```

## API List

REST API는 프론트엔드 명세에 맞춰 공통 wrapper 형식으로 응답합니다.

단건 응답:

```json
{
  "success": true,
  "data": {},
  "message": null,
  "error": null,
  "timestamp": "2026-06-18T09:30:00+09:00"
}
```

목록 응답:

```json
{
  "success": true,
  "data": {
    "items": [],
    "totalCount": 0
  },
  "message": null,
  "error": null,
  "timestamp": "2026-06-18T09:30:00+09:00"
}
```

프론트 명세 기준 주요 API:

- `GET /api/drains`
  - `ApiListResponse<DrainListItemDto>`
  - 각 item은 `id`, `roadAddress`, `fullAddress`, `latitude`, `longitude`, `riskLevel`, `riskScore`, `obstructionRatio`, `waterLevelCm`, `flowVelocityMps`, `finalDecision`, `updatedAt` 포함
- `GET /api/drains/{id}`
  - `ApiResponse<DrainDetailDto>`
  - 기본 하수구 필드와 `imageUrl`, `sensorSummary`, `sensorHistory`, `yoloResult`, `xgboostResult`, `riskHistory` 포함
- `GET /api/drains/{id}/sensors`
  - `ApiListResponse<SensorHistoryDto>`
  - `limit` query를 적용하며 `range` query는 MVP 이후 기간 필터링에 반영 예정
  - 기존 `GET /api/drains/{id}/sensor-data`도 alias로 유지
- `GET /api/drains/{id}/risk-history`
  - `ApiListResponse<RiskHistoryDto>`
  - 각 item은 `changedAt`, `riskLevel`, `riskScore` 중심으로 반환
  - `limit` query를 적용하며 `days` query는 MVP 이후 기간 필터링에 반영 예정
- `GET /api/dashboard/summary`
  - `ApiResponse<DashboardSummaryDto>`
  - `totalCount`, `goodCount`, `cautionCount`, `dangerCount`, `unknownCount`, `latestUpdatedAt` 포함
- `GET /api/drains/{id}/analysis/latest`
  - `ApiResponse<AnalysisResultDto>`
  - `sensorSummary`, `yoloResult`, `xgboostResult`, `updatedAt` 포함
- `WS /ws/drains/status`
  - 이벤트 타입: `DRAIN_STATUS_UPDATED`
  - payload는 `drainId`, `riskLevel`, `riskScore`, `waterLevelCm`, `flowVelocityMps`, `obstructionRatio`, `finalDecision`, `updatedAt` 포함

기존 호환 API:

- `GET /`
- `POST /api/drains`
- `POST /api/sensor-data`
- `GET /api/drains/{id}/sensor-data`
- `GET /api/drains/{id}/sensor-data/latest`
- `POST /api/analysis/yolo`
- `POST /api/analysis/xgboost`
- `GET /api/drains/{id}/yolo-results`
- `GET /api/drains/{id}/risk/latest`
- `GET /api/dashboard/drain-status`

## API Implementation Notes

- `POST /api/drains`, `POST /api/sensor-data`, `POST /api/analysis/yolo`, `POST /api/analysis/xgboost`는 camelCase와 snake_case 요청 body를 모두 허용합니다.
- `riskLevel`은 `good`, `caution`, `danger`, `unknown`만 사용합니다.
- `yoloStatus`는 `clear`, `partially_blocked`, `blocked`, `unknown`만 사용하며 `riskLevel`과 별도로 정규화합니다.
- `YoloResultDto`는 `analyzedAt`, `XgboostResultDto`는 `predictedAt`을 포함합니다.
- 에러 응답은 `error.code`, `error.message`, `error.detail`을 포함하는 공통 wrapper로 반환합니다.

## AI Stubs

`backend/app/ai/yolo_model.py`와 `backend/app/ai/xgboost_model.py`는 실제 모델 파일이 없어도 서버가 실행되도록 더미/규칙 기반 함수로 작성되어 있습니다. 추후 `best.pt`, `xgboost_model.pkl` 로딩 로직을 해당 파일에 연결하면 됩니다.
