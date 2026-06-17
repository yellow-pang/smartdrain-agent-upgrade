from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SensorData(Base):
    __tablename__ = "sensor_data"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    drain_id: Mapped[int] = mapped_column(ForeignKey("drains.id"), index=True)
    water_level_cm: Mapped[float] = mapped_column(Float)
    flow_velocity_mps: Mapped[float] = mapped_column(Float)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    drain = relationship("Drain", back_populates="sensor_data")
    xgboost_results = relationship("XgboostResult", back_populates="sensor_data")
