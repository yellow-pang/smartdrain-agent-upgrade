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
from app.schemas.dashboard import DashboardDrainStatus, DashboardSummary
from app.services import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)):
    return dashboard_service.get_dashboard_summary(db)


@router.get("/drain-status", response_model=list[DashboardDrainStatus])
def dashboard_drain_status(db: Session = Depends(get_db)):
    return dashboard_service.get_drain_status(db)
