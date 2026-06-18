"""
하수구 위험도 평가 결과를 생성하고 조회하는 서비스 파일입니다.

주요 역할:
- 센서 데이터와 YOLO 결과를 이용한 위험도 평가
- 위험도 결과 저장 및 하수구 상태 갱신
- 하수구별 위험도 이력과 최신 결과 조회
"""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ai.xgboost_model import predict_risk
from app.models.sensor_data import SensorData
from app.models.xgboost_result import XgboostResult
from app.models.yolo_result import YoloResult
from app.schemas.xgboost_result import XgboostResultCreate
from app.services.drain_service import get_drain
from app.services.sensor_service import get_latest_sensor_data
from app.services.yolo_service import get_latest_yolo_result


def _decision_text(risk_level: str) -> str:
    return {
        "danger": "Immediate field inspection is recommended.",
        "caution": "Monitor closely and schedule preventive maintenance.",
        "good": "No urgent action is required.",
        "unknown": "Risk could not be determined with current confidence.",
    }.get(risk_level, "Risk level is unavailable.")


def evaluate_risk(db: Session, payload: XgboostResultCreate) -> XgboostResult:
    drain = get_drain(db, payload.drain_id)

    sensor_data = db.get(SensorData, payload.sensor_data_id) if payload.sensor_data_id else get_latest_sensor_data(db, payload.drain_id)
    yolo_result = db.get(YoloResult, payload.yolo_result_id) if payload.yolo_result_id else get_latest_yolo_result(db, payload.drain_id)

    if not sensor_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor data not found")
    if not yolo_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="YOLO result not found")

    prediction = predict_risk(
        obstruction_ratio=yolo_result.obstruction_ratio,
        confidence_score=yolo_result.confidence_score,
        water_level_cm=sensor_data.water_level_cm,
        flow_velocity_mps=sensor_data.flow_velocity_mps,
    )

    result = XgboostResult(
        drain_id=payload.drain_id,
        sensor_data_id=sensor_data.id,
        yolo_result_id=yolo_result.id,
        risk_score=prediction["risk_score"],
        risk_level=prediction["risk_level"],
        final_decision=_decision_text(prediction["risk_level"]),
        evaluated_at=datetime.now(timezone.utc),
    )
    drain.status = prediction["risk_level"]
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def get_risk_history(db: Session, drain_id: int) -> list[XgboostResult]:
    get_drain(db, drain_id)
    return (
        db.query(XgboostResult)
        .filter(XgboostResult.drain_id == drain_id)
        .order_by(XgboostResult.evaluated_at.desc())
        .all()
    )


def get_latest_risk(db: Session, drain_id: int) -> XgboostResult:
    get_drain(db, drain_id)
    risk = (
        db.query(XgboostResult)
        .filter(XgboostResult.drain_id == drain_id)
        .order_by(XgboostResult.evaluated_at.desc())
        .first()
    )
    if not risk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk result not found")
    return risk
