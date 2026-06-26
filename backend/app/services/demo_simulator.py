from __future__ import annotations

import asyncio
import json
import logging
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.analysis_job import AnalysisJob
from app.models.drain import Drain
from app.models.sensor_data import SensorData
from app.models.xgboost_result import XgboostResult
from app.models.yolo_result import YoloResult
from app.schemas.api_response import drain_status_event_payload, format_datetime
from app.services import analysis_async_service
from app.websocket.events import DRAIN_STATUS_UPDATED, XGBOOST_RESULT_UPDATED, YOLO_RESULT_UPDATED
from app.websocket.manager import manager

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT_DIR = Path(__file__).resolve().parents[3]
DEMO_IMAGE_SOURCE_DIR = PROJECT_ROOT_DIR / "mock_data" / "ai_image_samples" / "demo"
DEMO_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")


@dataclass(frozen=True)
class DemoScenario:
    drain_code: str
    risk_level: str
    risk_score: float
    water_level_cm: float
    flow_velocity_mps: float
    obstruction_ratio: float
    confidence_score: float
    yolo_status: str
    final_decision: str


OVERVIEW_SCENARIOS: tuple[DemoScenario, ...] = (
    DemoScenario("DR-001", "good", 0.16, 24, 1.15, 0.14, 0.94, "clear", "normal"),
    DemoScenario("DR-002", "caution", 0.58, 55, 0.45, 0.58, 0.91, "partially_blocked", "field_check"),
    DemoScenario("DR-003", "good", 0.18, 26, 1.08, 0.16, 0.93, "clear", "normal"),
    DemoScenario("DR-004", "danger", 0.91, 82, 0.12, 0.86, 0.94, "blocked", "dispatch_required"),
    DemoScenario("DR-005", "unknown", 0.0, 12, 0.05, 0.0, 0.30, "unknown", "monitoring"),
)

STORY_SCENARIOS: tuple[DemoScenario, ...] = (
    DemoScenario("DR-003", "good", 0.18, 24, 1.15, 0.16, 0.93, "clear", "normal"),
    DemoScenario("DR-003", "caution", 0.62, 55, 0.45, 0.62, 0.90, "partially_blocked", "field_check"),
    DemoScenario("DR-003", "danger", 0.92, 82, 0.12, 0.88, 0.94, "blocked", "dispatch_required"),
    DemoScenario("DR-003", "unknown", 0.0, 18, 0.20, 0.0, 0.30, "unknown", "monitoring"),
    DemoScenario("DR-003", "caution", 0.54, 48, 0.55, 0.48, 0.88, "partially_blocked", "field_check"),
)

ACTIVE_JOB_STATUSES = {"processing", "yolo_completed"}
SUPPORTED_MODES = {"direct", "async"}
SENSOR_RANGES = {
    "good": ((18.0, 32.0), (0.95, 1.35)),
    "caution": ((48.0, 64.0), (0.35, 0.65)),
    "danger": ((76.0, 90.0), (0.05, 0.22)),
    "unknown": ((0.0, 20.0), (0.0, 0.25)),
}
ANALYSIS_RANGES = {
    "good": ((0.12, 0.24), (0.10, 0.22), (0.90, 0.96)),
    "caution": ((0.52, 0.68), (0.48, 0.66), (0.86, 0.93)),
    "danger": ((0.86, 0.96), (0.80, 0.92), (0.90, 0.96)),
    "unknown": ((0.0, 0.08), (0.0, 0.08), (0.25, 0.38)),
}


def start_demo_simulator(app) -> None:
    if not settings.DEMO_SIMULATOR_ENABLED:
        LOGGER.info("Demo simulator is disabled")
        return

    mode = settings.DEMO_SIMULATOR_MODE.strip().lower()
    if mode not in SUPPORTED_MODES:
        LOGGER.warning("Demo simulator mode '%s' is invalid; falling back to direct", mode)
        mode = "direct"

    app.state.demo_simulator_task = asyncio.create_task(_demo_loop(mode))
    LOGGER.info(
        "Demo simulator started: mode=%s interval=%ss start_delay=%ss target=%s",
        mode,
        settings.DEMO_SIMULATOR_INTERVAL_SECONDS,
        settings.DEMO_SIMULATOR_START_DELAY_SECONDS,
        settings.DEMO_SIMULATOR_TARGET_DRAIN_CODE,
    )


async def stop_demo_simulator(app) -> None:
    task = getattr(app.state, "demo_simulator_task", None)
    if task is None:
        return

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        LOGGER.info("Demo simulator stopped")


async def _demo_loop(mode: str) -> None:
    await asyncio.sleep(settings.DEMO_SIMULATOR_START_DELAY_SECONDS)
    await _run_overview(mode)

    step = 0
    while True:
        await asyncio.sleep(settings.DEMO_SIMULATOR_INTERVAL_SECONDS)
        scenario = STORY_SCENARIOS[step % len(STORY_SCENARIOS)]
        await _apply_scenario(mode, scenario)
        step += 1


async def _run_overview(mode: str) -> None:
    for scenario in OVERVIEW_SCENARIOS:
        await _apply_scenario(mode, scenario)
        await asyncio.sleep(0.2)


async def _apply_scenario(mode: str, scenario: DemoScenario) -> None:
    sampled_scenario = _sample_scenario(scenario)
    try:
        with SessionLocal() as db:
            drain = _get_drain_by_code(db, sampled_scenario.drain_code)
            if drain is None:
                LOGGER.warning("Demo simulator skipped missing drain: %s", sampled_scenario.drain_code)
                return

            if mode == "async":
                await _apply_async_scenario(db, drain, sampled_scenario)
                return

            await _apply_direct_scenario(db, drain, sampled_scenario)
    except asyncio.CancelledError:
        raise
    except Exception:
        LOGGER.exception("Demo simulator step failed: drain_code=%s", sampled_scenario.drain_code)


async def _apply_async_scenario(db: Session, drain: Drain, scenario: DemoScenario) -> None:
    if _has_active_job(db, drain.id):
        LOGGER.info("Demo simulator skipped active analysis job: drain_code=%s", scenario.drain_code)
        return

    sensor_data = _create_sensor_data(db, drain.id, scenario)
    db.commit()
    db.refresh(sensor_data)
    await analysis_async_service.start_analysis_for_drain(db, drain, trigger_type="demo")


async def _apply_direct_scenario(db: Session, drain: Drain, scenario: DemoScenario) -> None:
    now = datetime.now(timezone.utc)
    sensor_data = _create_sensor_data(db, drain.id, scenario, measured_at=now)
    db.flush()

    yolo_result = YoloResult(
        drain_id=drain.id,
        image_url=_mock_image_url(drain.id, scenario.risk_level),
        obstruction_ratio=scenario.obstruction_ratio,
        confidence_score=scenario.confidence_score,
        yolo_status=scenario.yolo_status,
        captured_at=now,
    )
    db.add(yolo_result)
    db.flush()

    xgboost_result = XgboostResult(
        drain_id=drain.id,
        sensor_data_id=sensor_data.id,
        yolo_result_id=yolo_result.id,
        risk_score=scenario.risk_score,
        risk_level=scenario.risk_level,
        final_decision=scenario.final_decision,
        evaluated_at=now,
    )
    drain.status = scenario.risk_level
    db.add(xgboost_result)
    db.flush()

    request_id = _create_demo_request_id(drain.id, now)
    job = AnalysisJob(
        request_id=request_id,
        job_id=f"AI_JOB_{request_id}",
        drain_id=drain.id,
        sensor_data_id=sensor_data.id,
        sensor_measured_at=sensor_data.measured_at,
        yolo_result_id=yolo_result.id,
        status="completed",
        trigger_type="demo",
    )
    db.add(job)
    db.commit()
    db.refresh(yolo_result)
    db.refresh(xgboost_result)

    await _broadcast_events(db, drain, sensor_data, yolo_result, xgboost_result)
    LOGGER.info(
        "Demo simulator applied: drain_code=%s risk=%s water=%s flow=%s",
        scenario.drain_code,
        scenario.risk_level,
        scenario.water_level_cm,
        scenario.flow_velocity_mps,
    )


def _create_sensor_data(
    db: Session,
    drain_id: int,
    scenario: DemoScenario,
    measured_at: datetime | None = None,
) -> SensorData:
    sensor_data = SensorData(
        drain_id=drain_id,
        water_level_cm=scenario.water_level_cm,
        flow_velocity_mps=scenario.flow_velocity_mps,
        measured_at=measured_at or datetime.now(timezone.utc),
    )
    db.add(sensor_data)
    return sensor_data


def _sample_scenario(scenario: DemoScenario) -> DemoScenario:
    sensor_ranges = SENSOR_RANGES.get(scenario.risk_level)
    analysis_ranges = ANALYSIS_RANGES.get(scenario.risk_level)
    if sensor_ranges is None or analysis_ranges is None:
        return scenario

    water_level_range, flow_velocity_range = sensor_ranges
    risk_score_range, obstruction_ratio_range, confidence_score_range = analysis_ranges

    return DemoScenario(
        drain_code=scenario.drain_code,
        risk_level=scenario.risk_level,
        risk_score=_sample_float(*risk_score_range, digits=4),
        water_level_cm=_sample_float(*water_level_range, digits=1),
        flow_velocity_mps=_sample_float(*flow_velocity_range, digits=2),
        obstruction_ratio=_sample_float(*obstruction_ratio_range, digits=4),
        confidence_score=_sample_float(*confidence_score_range, digits=4),
        yolo_status=scenario.yolo_status,
        final_decision=scenario.final_decision,
    )


def _sample_float(minimum: float, maximum: float, digits: int) -> float:
    return round(random.uniform(minimum, maximum), digits)


async def _broadcast_events(
    db: Session,
    drain: Drain,
    sensor_data: SensorData,
    yolo_result: YoloResult,
    xgboost_result: XgboostResult,
) -> None:
    yolo_event = {
        "type": YOLO_RESULT_UPDATED,
        "payload": {
            "drainId": drain.drain_code,
            "yoloResultId": yolo_result.id,
            "imageUrl": yolo_result.image_url,
            "obstructionRatio": yolo_result.obstruction_ratio,
            "confidenceScore": yolo_result.confidence_score,
            "yoloStatus": yolo_result.yolo_status,
            "capturedAt": format_datetime(yolo_result.captured_at),
            "analyzedAt": format_datetime(yolo_result.created_at),
            "updatedAt": format_datetime(yolo_result.created_at),
        },
    }
    xgboost_event = {
        "type": XGBOOST_RESULT_UPDATED,
        "payload": {
            "drainId": drain.drain_code,
            "xgboostResultId": xgboost_result.id,
            "sensorDataId": xgboost_result.sensor_data_id,
            "yoloResultId": xgboost_result.yolo_result_id,
            "riskLevel": xgboost_result.risk_level,
            "riskScore": xgboost_result.risk_score,
            "finalDecision": xgboost_result.final_decision,
            "evaluatedAt": format_datetime(xgboost_result.evaluated_at),
            "updatedAt": format_datetime(xgboost_result.evaluated_at),
        },
    }
    status_event = drain_status_event_payload(
        db,
        drain,
        xgboost_result,
        sensor_data=sensor_data,
        yolo_result=yolo_result,
    )
    status_event["type"] = DRAIN_STATUS_UPDATED

    for event in (yolo_event, xgboost_event, status_event):
        await manager.broadcast(json.dumps(event))


def _get_drain_by_code(db: Session, drain_code: str) -> Drain | None:
    return db.query(Drain).filter(Drain.drain_code == drain_code).first()


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


def _mock_image_url(drain_id: int, risk_level: str) -> str:
    for extension in DEMO_IMAGE_EXTENSIONS:
        image_path = DEMO_IMAGE_SOURCE_DIR / f"drain_{drain_id}_{risk_level}{extension}"
        if image_path.is_file():
            return f"/api/mock-images/demo/{image_path.name}"
    return f"/api/mock-images/drain_{drain_id}.jpg"


def _create_demo_request_id(drain_id: int, value: datetime) -> str:
    timestamp = value.strftime("%Y%m%d%H%M%S%f")
    return f"REQ_DEMO_{timestamp}_{drain_id}"
