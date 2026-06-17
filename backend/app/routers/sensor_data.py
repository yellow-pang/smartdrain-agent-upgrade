from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.sensor_data import SensorDataCreate, SensorDataResponse
from app.services import sensor_service

router = APIRouter(prefix="/api", tags=["sensor-data"])


@router.post("/sensor-data", response_model=SensorDataResponse, status_code=201)
def create_sensor_data(payload: SensorDataCreate, db: Session = Depends(get_db)):
    return sensor_service.create_sensor_data(db, payload)


@router.get("/drains/{drain_id}/sensor-data", response_model=list[SensorDataResponse])
def list_sensor_data(drain_id: int, db: Session = Depends(get_db)):
    return sensor_service.get_sensor_data_by_drain(db, drain_id)


@router.get("/drains/{drain_id}/sensor-data/latest", response_model=SensorDataResponse)
def latest_sensor_data(drain_id: int, db: Session = Depends(get_db)):
    return sensor_service.get_latest_sensor_data(db, drain_id)
