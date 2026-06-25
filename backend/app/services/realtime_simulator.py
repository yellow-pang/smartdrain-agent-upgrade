"""
실시간 대시보드 자동 시뮬레이터를 관리합니다.

주요 역할:
- 주기적으로 센서 데이터를 생성하고 비동기 분석 요청을 시작
- 런타임 start/stop/status 제어
- 수동 분석 흐름을 유지하면서 자동 모드를 추가
"""

from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.analysis_job import AnalysisJob
from app.models.drain import Drain
from app.models.sensor_data import SensorData
from app.schemas.api_response import format_datetime
from app.services import analysis_async_service

LOGGER = logging.getLogger(__name__)
ACTIVE_JOB_STATUSES = {"processing", "yolo_completed"}
DEFAULT_INTERVAL_SECONDS = 20
MIN_WATER_LEVEL_CM = 5.0
MAX_WATER_LEVEL_CM = 95.0
MIN_FLOW_VELOCITY_MPS = 0.1
MAX_FLOW_VELOCITY_MPS = 4.5


@dataclass
class RealtimeSimulatorRuntime:
    task: asyncio.Task | None = None
    interval_seconds: int = DEFAULT_INTERVAL_SECONDS
    started_at: datetime | None = None
    last_tick_at: datetime | None = None
    last_run_drain_count: int = 0
    total_run_count: int = 0
    last_error: str | None = None


_runtime = RealtimeSimulatorRuntime()
_runtime_lock = asyncio.Lock()
_rng = random.Random()


async def start_realtime_simulator(interval_seconds: int | None = None) -> tuple[dict[str, object], bool]:
    async with _runtime_lock:
        if _runtime.task is not None and not _runtime.task.done():
            return get_realtime_simulator_status(), False

        _runtime.interval_seconds = interval_seconds or DEFAULT_INTERVAL_SECONDS
        _runtime.started_at = datetime.now(timezone.utc)
        _runtime.last_tick_at = None
        _runtime.last_run_drain_count = 0
        _runtime.total_run_count = 0
        _runtime.last_error = None
        _runtime.task = asyncio.create_task(_simulator_loop())
        LOGGER.info("Realtime simulator started (interval=%s sec)", _runtime.interval_seconds)
        return get_realtime_simulator_status(), True


async def stop_realtime_simulator() -> tuple[dict[str, object], bool]:
    task: asyncio.Task | None = None
    async with _runtime_lock:
        if _runtime.task is None or _runtime.task.done():
            _runtime.task = None
            return get_realtime_simulator_status(), False
        task = _runtime.task
        _runtime.task = None

    if task is not None:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            LOGGER.info("Realtime simulator stopped")
    return get_realtime_simulator_status(), True


async def shutdown_realtime_simulator() -> None:
    await stop_realtime_simulator()


def get_realtime_simulator_status() -> dict[str, object]:
    running = _runtime.task is not None and not _runtime.task.done()
    return {
        "running": running,
        "intervalSeconds": _runtime.interval_seconds,
        "startedAt": format_datetime(_runtime.started_at),
        "lastTickAt": format_datetime(_runtime.last_tick_at),
        "lastRunDrainCount": _runtime.last_run_drain_count,
        "totalRunCount": _runtime.total_run_count,
        "lastError": _runtime.last_error,
        "triggerType": "scheduled",
    }


async def _simulator_loop() -> None:
    while True:
        try:
            generated = await _run_once()
            _runtime.last_run_drain_count = generated
            _runtime.total_run_count += 1
            _runtime.last_tick_at = datetime.now(timezone.utc)
            _runtime.last_error = None
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            _runtime.last_error = str(exc)
            LOGGER.exception("Realtime simulator tick failed")
        await asyncio.sleep(_runtime.interval_seconds)


async def _run_once() -> int:
    generated = 0
    with SessionLocal() as db:
        drains = db.query(Drain).order_by(Drain.id.asc()).all()
        for drain in drains:
            if _has_active_job(db, drain.id):
                continue
            _create_simulated_sensor_data(db, drain.id)
            try:
                await analysis_async_service.start_analysis_for_drain(db, drain, trigger_type="scheduled")
                generated += 1
            except HTTPException as exc:
                LOGGER.warning("Realtime simulator analysis skipped drain_id=%s detail=%s", drain.id, exc.detail)
            except Exception:
                db.rollback()
                LOGGER.exception("Realtime simulator analysis failed drain_id=%s", drain.id)
    return generated


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


def _create_simulated_sensor_data(db: Session, drain_id: int) -> SensorData:
    latest = (
        db.query(SensorData)
        .filter(SensorData.drain_id == drain_id)
        .order_by(SensorData.measured_at.desc())
        .first()
    )
    water_level_base = latest.water_level_cm if latest else 20.0 + (drain_id % 5) * 8.0
    flow_velocity_base = latest.flow_velocity_mps if latest else 0.8 + (drain_id % 3) * 0.5

    sensor_data = SensorData(
        drain_id=drain_id,
        water_level_cm=_clamp(water_level_base + _rng.uniform(-7.0, 9.0), MIN_WATER_LEVEL_CM, MAX_WATER_LEVEL_CM),
        flow_velocity_mps=_clamp(
            flow_velocity_base + _rng.uniform(-0.35, 0.45),
            MIN_FLOW_VELOCITY_MPS,
            MAX_FLOW_VELOCITY_MPS,
        ),
        measured_at=datetime.now(timezone.utc),
    )
    db.add(sensor_data)
    db.commit()
    db.refresh(sensor_data)
    return sensor_data


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
