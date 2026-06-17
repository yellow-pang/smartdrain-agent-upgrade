import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.xgboost_result import XgboostResultCreate, XgboostResultResponse
from app.schemas.yolo_result import YoloResultCreate, YoloResultResponse
from app.services import xgboost_service, yolo_service
from app.websocket.manager import manager

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analysis/yolo", response_model=YoloResultResponse, status_code=201)
def create_yolo_result(payload: YoloResultCreate, db: Session = Depends(get_db)):
    return yolo_service.create_yolo_result(db, payload)


@router.post("/analysis/xgboost", response_model=XgboostResultResponse, status_code=201)
async def create_xgboost_result(payload: XgboostResultCreate, db: Session = Depends(get_db)):
    result = xgboost_service.evaluate_risk(db, payload)
    await manager.broadcast(
        json.dumps(
            {
                "type": "risk_update",
                "drain_id": result.drain_id,
                "risk_score": result.risk_score,
                "risk_level": result.risk_level,
            }
        )
    )
    return result


@router.get("/drains/{drain_id}/yolo-results", response_model=list[YoloResultResponse])
def list_yolo_results(drain_id: int, db: Session = Depends(get_db)):
    return yolo_service.get_yolo_results_by_drain(db, drain_id)


@router.get("/drains/{drain_id}/risk-history", response_model=list[XgboostResultResponse])
def risk_history(drain_id: int, db: Session = Depends(get_db)):
    return xgboost_service.get_risk_history(db, drain_id)


@router.get("/drains/{drain_id}/risk/latest", response_model=XgboostResultResponse)
def latest_risk(drain_id: int, db: Session = Depends(get_db)):
    return xgboost_service.get_latest_risk(db, drain_id)
