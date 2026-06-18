"""
대시보드 화면에 필요한 데이터를 계산하는 서비스 파일입니다.

주요 역할:
- 하수구 상태별 개수 요약 생성
- 하수구별 기본 정보와 최신 위험도 정보 조회
- 대시보드 응답 스키마 객체 구성
"""

from sqlalchemy.orm import Session

from app.models.drain import Drain
from app.models.xgboost_result import XgboostResult
from app.schemas.dashboard import DashboardDrainStatus, DashboardSummary


def get_dashboard_summary(db: Session) -> DashboardSummary:
    drains = db.query(Drain).all()
    counts = {"good": 0, "caution": 0, "danger": 0, "unknown": 0}
    for drain in drains:
        counts[drain.status if drain.status in counts else "unknown"] += 1
    return DashboardSummary(total_drains=len(drains), **{f"{key}_count": value for key, value in counts.items()})


def get_drain_status(db: Session) -> list[DashboardDrainStatus]:
    drains = db.query(Drain).order_by(Drain.id).all()
    statuses: list[DashboardDrainStatus] = []
    for drain in drains:
        latest_risk = (
            db.query(XgboostResult)
            .filter(XgboostResult.drain_id == drain.id)
            .order_by(XgboostResult.evaluated_at.desc())
            .first()
        )
        statuses.append(
            DashboardDrainStatus(
                drain_id=drain.id,
                drain_code=drain.drain_code,
                name=drain.name,
                address=drain.address,
                latitude=drain.latitude,
                longitude=drain.longitude,
                status=drain.status,
                latest_risk_score=latest_risk.risk_score if latest_risk else None,
                latest_risk_level=latest_risk.risk_level if latest_risk else None,
            )
        )
    return statuses
