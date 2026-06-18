"""
하수구 테이블을 정의하는 SQLAlchemy 모델 파일입니다.

주요 역할:
- 하수구 기본 정보와 상태 컬럼 정의
- 생성 및 수정 시각 컬럼 정의
- 센서 데이터, YOLO 결과, XGBoost 결과와의 관계 설정
"""

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
