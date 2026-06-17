from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class XgboostResult(Base):
    __tablename__ = "xgboost_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    drain_id: Mapped[int] = mapped_column(ForeignKey("drains.id"), index=True)
    sensor_data_id: Mapped[int | None] = mapped_column(ForeignKey("sensor_data.id"), nullable=True, index=True)
    yolo_result_id: Mapped[int | None] = mapped_column(ForeignKey("yolo_results.id"), nullable=True, index=True)
    risk_score: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String(20), default="unknown", index=True)
    final_decision: Mapped[str] = mapped_column(String(255))
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    drain = relationship("Drain", back_populates="xgboost_results")
    sensor_data = relationship("SensorData", back_populates="xgboost_results")
    yolo_result = relationship("YoloResult", back_populates="xgboost_results")
