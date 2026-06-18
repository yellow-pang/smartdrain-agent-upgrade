"""
센서 데이터 생성과 조회를 담당하는 서비스 파일입니다.

주요 역할:
- 하수구 존재 여부 확인 후 센서 데이터 저장
- 하수구별 센서 데이터 목록 조회
- 하수구별 최신 센서 데이터 조회 및 미존재 시 예외 처리
"""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.sensor_data import SensorData
from app.schemas.sensor_data import SensorDataCreate
from app.services.drain_service import get_drain


def create_sensor_data(db: Session, payload: SensorDataCreate) -> SensorData:
    get_drain(db, payload.drain_id)
    data = payload.model_dump()
    data["measured_at"] = data["measured_at"] or datetime.now(timezone.utc)
    sensor_data = SensorData(**data)
    db.add(sensor_data)
    db.commit()
    db.refresh(sensor_data)
    return sensor_data


def get_sensor_data_by_drain(db: Session, drain_id: int) -> list[SensorData]:
    get_drain(db, drain_id)
    return (
        db.query(SensorData)
        .filter(SensorData.drain_id == drain_id)
        .order_by(SensorData.measured_at.desc())
        .all()
    )


def get_latest_sensor_data(db: Session, drain_id: int) -> SensorData:
    get_drain(db, drain_id)
    sensor_data = (
        db.query(SensorData)
        .filter(SensorData.drain_id == drain_id)
        .order_by(SensorData.measured_at.desc())
        .first()
    )
    if not sensor_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor data not found")
    return sensor_data
