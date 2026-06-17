from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Drain(Base):
    __tablename__ = "drains"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    drain_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="unknown", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    sensor_data = relationship("SensorData", back_populates="drain", cascade="all, delete-orphan")
    yolo_results = relationship("YoloResult", back_populates="drain", cascade="all, delete-orphan")
    xgboost_results = relationship("XgboostResult", back_populates="drain", cascade="all, delete-orphan")
