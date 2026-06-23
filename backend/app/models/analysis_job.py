"""
AI 서버 비동기 분석 요청 상태를 저장하는 SQLAlchemy 모델 파일입니다.

주요 역할:
- request_id와 job_id 기반 분석 요청 매핑 저장
- drain, sensor_data, yolo_result 연결 정보 저장
- 비동기 분석 진행 상태, 트리거 유형, 오류 메시지 관리
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    request_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    job_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    drain_id: Mapped[int] = mapped_column(ForeignKey("drains.id"), index=True)
    sensor_data_id: Mapped[int] = mapped_column(ForeignKey("sensor_data.id"), index=True)
    sensor_measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    yolo_result_id: Mapped[int | None] = mapped_column(ForeignKey("yolo_results.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(40), default="processing", index=True)
    trigger_type: Mapped[str] = mapped_column(String(20), default="manual", index=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    drain = relationship("Drain")
    sensor_data = relationship("SensorData")
    yolo_result = relationship("YoloResult")
