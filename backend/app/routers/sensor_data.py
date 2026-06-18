"""
센서 데이터 API를 처리하는 라우터 파일입니다.

주요 역할:
- 센서 데이터 등록 API 정의
- 하수구별 센서 데이터 목록 조회 API 정의
- 하수구별 최신 센서 데이터 조회 API 정의
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.api_response import api_list_response, api_response, sensor_data_dto
from app.schemas.sensor_data import SensorDataCreate
from app.services import sensor_service
from app.services.drain_service import get_drain_by_identifier

router = APIRouter(prefix="/api", tags=["sensor-data"])


@router.post("/sensor-data", status_code=201)
def create_sensor_data(payload: SensorDataCreate, db: Session = Depends(get_db)):
    sensor_data = sensor_service.create_sensor_data(db, payload)
    return api_response(sensor_data_dto(sensor_data), message="Sensor data created")


@router.get("/drains/{drain_id}/sensors")
@router.get("/drains/{drain_id}/sensor-data")
def list_sensor_data(drain_id: str, db: Session = Depends(get_db)):
    drain = get_drain_by_identifier(db, drain_id)
    sensor_data = sensor_service.get_sensor_data_by_drain(db, drain.id)
    return api_list_response([sensor_data_dto(item) for item in sensor_data])


@router.get("/drains/{drain_id}/sensor-data/latest")
def latest_sensor_data(drain_id: str, db: Session = Depends(get_db)):
    drain = get_drain_by_identifier(db, drain_id)
    sensor_data = sensor_service.get_latest_sensor_data(db, drain.id)
    return api_response(sensor_data_dto(sensor_data))
