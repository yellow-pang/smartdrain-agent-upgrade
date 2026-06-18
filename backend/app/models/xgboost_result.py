"""
XGBoost 위험도 평가 결과 테이블을 정의하는 SQLAlchemy 모델 파일입니다.

주요 역할:
- 하수구, 센서 데이터, YOLO 결과 참조 컬럼 정의
- 위험 점수, 위험 등급, 최종 판단 컬럼 정의
- 관련 모델과의 관계 설정
"""

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
