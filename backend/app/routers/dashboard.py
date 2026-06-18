"""
대시보드 조회 API를 처리하는 라우터 파일입니다.

주요 역할:
- 전체 하수구 상태 요약 API 정의
- 하수구별 대시보드 상태 조회 API 정의
- 요청을 대시보드 서비스 계층으로 전달
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.drain import Drain
from app.models.xgboost_result import XgboostResult
from app.schemas.api_response import api_list_response, api_response, drain_list_item_dto, format_datetime
from app.services import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    summary = dashboard_service.get_dashboard_summary(db)
    latest_risk = db.query(XgboostResult).order_by(XgboostResult.evaluated_at.desc()).first()
    latest_drain = db.query(Drain).order_by(Drain.updated_at.desc()).first()
    latest_updated_at = latest_risk.evaluated_at if latest_risk else latest_drain.updated_at if latest_drain else None
    return api_response(
        {
            "totalCount": summary.total_drains,
            "goodCount": summary.good_count,
            "cautionCount": summary.caution_count,
            "dangerCount": summary.danger_count,
            "unknownCount": summary.unknown_count,
            "latestUpdatedAt": format_datetime(latest_updated_at),
        }
    )


@router.get("/drain-status")
def dashboard_drain_status(db: Session = Depends(get_db)):
    drains = db.query(Drain).order_by(Drain.id).all()
    return api_list_response([drain_list_item_dto(db, drain) for drain in drains])
