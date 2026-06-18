# SmartDrain Backend

## Seed Mock Data

프론트-백엔드 연동 테스트 전에 PostgreSQL DB에 대시보드와 상세 화면 확인용 목 데이터를 넣기 위한 seed 스크립트입니다.

생성되는 데이터:

- `DR-001`: `good`
- `DR-002`: `good`
- `DR-003`: `caution`
- `DR-004`: `danger`
- `DR-005`: `unknown`

각 빗물받이에 대해 `sensor_data`, `yolo_result`, `xgboost_result`가 함께 생성됩니다. 이미 같은 `drain_code`가 있으면 중복 생성하지 않고 건너뜁니다.

## 실행 전 준비

DB 테이블은 Alembic 마이그레이션으로 먼저 생성되어 있어야 합니다.

프로젝트 루트에서:

```bash
python -m alembic upgrade head
```

## 실행 명령어

프로젝트 루트에서:

```bash
cd backend
python -m app.seeds.seed_mock_data
```

## 실행 후 확인할 API

- `GET /api/drains`
- `GET /api/dashboard/summary`
- `GET /api/drains/DR-004`
- `GET /api/drains/DR-004/sensors`
- `GET /api/drains/DR-004/risk-history`
- `GET /api/drains/DR-004/analysis/latest`
