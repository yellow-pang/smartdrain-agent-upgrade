"""
센서 데이터 테이블을 정의하는 SQLAlchemy 모델 파일입니다.

주요 역할:
- 하수구별 수위와 유속 측정값 컬럼 정의
- 측정 시각과 생성 시각 컬럼 정의
- 하수구 및 XGBoost 결과 모델과의 관계 설정
"""

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
