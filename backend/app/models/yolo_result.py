from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class YoloResult(Base):
    __tablename__ = "yolo_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    drain_id: Mapped[int] = mapped_column(ForeignKey("drains.id"), index=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    obstruction_ratio: Mapped[float] = mapped_column(Float)
    confidence_score: Mapped[float] = mapped_column(Float)
    yolo_status: Mapped[str] = mapped_column(String(20), default="unknown")
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    drain = relationship("Drain", back_populates="yolo_results")
    xgboost_results = relationship("XgboostResult", back_populates="yolo_result")
