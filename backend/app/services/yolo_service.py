from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.ai.yolo_model import run_yolo_analysis
from app.models.yolo_result import YoloResult
from app.schemas.yolo_result import YoloResultCreate
from app.services.drain_service import get_drain


def create_yolo_result(db: Session, payload: YoloResultCreate) -> YoloResult:
    get_drain(db, payload.drain_id)
    analysis = run_yolo_analysis(payload.image_url)
    data = payload.model_dump()
    data["obstruction_ratio"] = data["obstruction_ratio"] if data["obstruction_ratio"] is not None else analysis["obstruction_ratio"]
    data["confidence_score"] = data["confidence_score"] if data["confidence_score"] is not None else analysis["confidence_score"]
    data["yolo_status"] = data["yolo_status"] or analysis["yolo_status"]
    data["captured_at"] = data["captured_at"] or datetime.now(timezone.utc)
    result = YoloResult(**data)
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def get_yolo_results_by_drain(db: Session, drain_id: int) -> list[YoloResult]:
    get_drain(db, drain_id)
    return (
        db.query(YoloResult)
        .filter(YoloResult.drain_id == drain_id)
        .order_by(YoloResult.captured_at.desc())
        .all()
    )


def get_latest_yolo_result(db: Session, drain_id: int) -> YoloResult | None:
    return (
        db.query(YoloResult)
        .filter(YoloResult.drain_id == drain_id)
        .order_by(YoloResult.captured_at.desc())
        .first()
    )
