"""
예약 기반 비동기 분석 job 생성을 담당하는 서비스 파일입니다.

주요 역할:
- 설정값에 따라 백그라운드 scheduler 실행 여부 결정
- 최신 센서 데이터와 기존 job 상태를 기준으로 scheduled 분석 대상 선별
- 오래된 processing/yolo_completed job timeout 처리
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.analysis_job import AnalysisJob
from app.models.drain import Drain
from app.models.sensor_data import SensorData
from app.services import analysis_async_service

ACTIVE_JOB_STATUSES = {"processing", "yolo_completed"}
LOGGER = logging.getLogger(__name__)


def start_analysis_scheduler(app) -> None:
    if not settings.ANALYSIS_SCHEDULER_ENABLED:
        LOGGER.info("Analysis scheduler is disabled")
        return
    app.state.analysis_scheduler_task = asyncio.create_task(_scheduler_loop())
    LOGGER.info("Analysis scheduler started")


async def stop_analysis_scheduler(app) -> None:
    task = getattr(app.state, "analysis_scheduler_task", None)
    if task is None:
        return
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        LOGGER.info("Analysis scheduler stopped")


async def _scheduler_loop() -> None:
    await asyncio.sleep(settings.ANALYSIS_SCHEDULER_INITIAL_DELAY_SECONDS)
    while True:
        try:
            with SessionLocal() as db:
                await run_scheduled_analysis_once(db)
        except asyncio.CancelledError:
            raise
        except Exception:
            LOGGER.exception("Analysis scheduler iteration failed")
        await asyncio.sleep(settings.ANALYSIS_SCHEDULER_INTERVAL_SECONDS)


async def run_scheduled_analysis_once(db: Session) -> None:
    mark_timed_out_jobs(db)
    drains = db.query(Drain).order_by(Drain.id.asc()).all()
    for drain in drains:
        sensor_data = _get_latest_sensor_data(db, drain.id)
        if sensor_data is None:
            continue
        if not _is_recent(sensor_data.measured_at, settings.ANALYSIS_SENSOR_MAX_AGE_SECONDS):
            continue
        if _has_active_job(db, drain.id):
            continue
        latest_job = _get_latest_job(db, drain.id)
        if latest_job is not None and _is_recent(latest_job.created_at, settings.ANALYSIS_SCHEDULER_INTERVAL_SECONDS):
            continue
        try:
            await analysis_async_service.start_analysis_for_drain(db, drain, trigger_type="scheduled")
        except HTTPException as exc:
            LOGGER.warning("Scheduled analysis failed for drain_id=%s: %s", drain.id, exc.detail)
        except Exception:
            db.rollback()
            LOGGER.exception("Scheduled analysis failed for drain_id=%s", drain.id)


def mark_timed_out_jobs(db: Session) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=settings.ANALYSIS_JOB_TIMEOUT_SECONDS)
    jobs = (
        db.query(AnalysisJob)
        .filter(
            AnalysisJob.status.in_(ACTIVE_JOB_STATUSES),
            AnalysisJob.updated_at < cutoff,
        )
        .all()
    )
    for job in jobs:
        job.status = "failed"
        job.error_message = f"Analysis job timed out after {settings.ANALYSIS_JOB_TIMEOUT_SECONDS} seconds"
    if jobs:
        db.commit()
    return len(jobs)


def _get_latest_sensor_data(db: Session, drain_id: int) -> SensorData | None:
    return (
        db.query(SensorData)
        .filter(SensorData.drain_id == drain_id)
        .order_by(SensorData.measured_at.desc())
        .first()
    )


def _has_active_job(db: Session, drain_id: int) -> bool:
    return (
        db.query(AnalysisJob)
        .filter(
            AnalysisJob.drain_id == drain_id,
            AnalysisJob.status.in_(ACTIVE_JOB_STATUSES),
        )
        .first()
        is not None
    )


def _get_latest_job(db: Session, drain_id: int) -> AnalysisJob | None:
    return (
        db.query(AnalysisJob)
        .filter(AnalysisJob.drain_id == drain_id)
        .order_by(AnalysisJob.created_at.desc())
        .first()
    )


def _is_recent(value: datetime, max_age_seconds: int) -> bool:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - value <= timedelta(seconds=max_age_seconds)
