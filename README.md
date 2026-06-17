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

- `GET /`
- `GET /api/drains`
- `GET /api/drains/{drain_id}`
- `POST /api/drains`
- `POST /api/sensor-data`
- `GET /api/drains/{drain_id}/sensor-data`
- `GET /api/drains/{drain_id}/sensor-data/latest`
- `POST /api/analysis/yolo`
- `POST /api/analysis/xgboost`
- `GET /api/drains/{drain_id}/yolo-results`
- `GET /api/drains/{drain_id}/risk-history`
- `GET /api/drains/{drain_id}/risk/latest`
- `GET /api/dashboard/summary`
- `GET /api/dashboard/drain-status`
- `WS /ws/drains/status`

## AI Stubs

`backend/app/ai/yolo_model.py`와 `backend/app/ai/xgboost_model.py`는 실제 모델 파일이 없어도 서버가 실행되도록 더미/규칙 기반 함수로 작성되어 있습니다. 추후 `best.pt`, `xgboost_model.pkl` 로딩 로직을 해당 파일에 연결하면 됩니다.
