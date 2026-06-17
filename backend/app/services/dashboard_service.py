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
