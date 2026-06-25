"""
실시간 대시보드 자동 시뮬레이터를 관리합니다.

주요 역할:
- 주기적으로 상태별 시나리오 센서/분석 결과를 생성
- 런타임 start/stop/status 제어
- 수동 분석 흐름을 유지하면서 자동 모드를 추가
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.analysis_job import AnalysisJob
from app.models.drain import Drain
from app.models.sensor_data import SensorData
from app.models.xgboost_result import XgboostResult
from app.models.yolo_result import YoloResult
from app.schemas.api_response import drain_status_event_payload, format_datetime
from app.websocket.events import XGBOOST_RESULT_UPDATED, YOLO_RESULT_UPDATED
from app.websocket.manager import manager

LOGGER = logging.getLogger(__name__)
ACTIVE_JOB_STATUSES = {"processing", "yolo_completed"}
DEFAULT_INTERVAL_SECONDS = 20
MOCK_IMAGE_URL_PREFIX = "/api/mock-images"
PROJECT_ROOT_DIR = Path(__file__).resolve().parents[3]
SCENARIO_IMAGE_ROOT_DIR = PROJECT_ROOT_DIR / "mock_data" / "ai_image_samples" / "scenarios"
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass(frozen=True)
class ScenarioProfile:
    risk_level: str
    water_level_range: tuple[float, float]
    flow_velocity_range: tuple[float, float]
    obstruction_ratio_range: tuple[float, float]
    confidence_score_range: tuple[float, float]
    risk_score_range: tuple[float, float]
    yolo_status: str
    final_decision: str


SCENARIO_PROFILES: tuple[ScenarioProfile, ...] = (
    ScenarioProfile(
        risk_level="good",
        water_level_range=(8.0, 28.0),
        flow_velocity_range=(0.9, 2.4),
        obstruction_ratio_range=(0.02, 0.24),
        confidence_score_range=(0.86, 0.98),
        risk_score_range=(0.05, 0.28),
        yolo_status="clear",
        final_decision="막힘과 수위가 낮아 정상 상태입니다.",
    ),
    ScenarioProfile(
        risk_level="caution",
        water_level_range=(35.0, 62.0),
        flow_velocity_range=(0.35, 1.2),
        obstruction_ratio_range=(0.42, 0.68),
        confidence_score_range=(0.78, 0.94),
        risk_score_range=(0.46, 0.69),
        yolo_status="partially_blocked",
        final_decision="일부 막힘 또는 수위 상승이 감지되어 주의 관찰이 필요합니다.",
    ),
    ScenarioProfile(
        risk_level="danger",
        water_level_range=(68.0, 95.0),
        flow_velocity_range=(0.05, 0.45),
        obstruction_ratio_range=(0.74, 0.96),
        confidence_score_range=(0.84, 0.99),
        risk_score_range=(0.78, 0.97),
        yolo_status="blocked",
        final_decision="막힘률과 수위가 높아 현장 조치가 필요합니다.",
    ),
    ScenarioProfile(
        risk_level="unknown",
        water_level_range=(0.0, 12.0),
        flow_velocity_range=(0.0, 0.25),
        obstruction_ratio_range=(0.0, 0.08),
        confidence_score_range=(0.12, 0.42),
        risk_score_range=(0.0, 0.12),
        yolo_status="unknown",
        final_decision="센서 또는 이미지 신뢰도가 낮아 위험도를 판단하기 어렵습니다.",
    ),
)


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
        "mode": "scenario",
        "imageRoot": str(SCENARIO_IMAGE_ROOT_DIR),
        "scenarioLevels": [profile.risk_level for profile in SCENARIO_PROFILES],
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
        for drain, scenario in zip(drains, _scenario_sequence(len(drains)), strict=False):
            if _has_active_job(db, drain.id):
                continue
            try:
                events = _create_simulated_scenario_results(db, drain, scenario)
                for event in events:
                    await manager.broadcast(json.dumps(event))
                generated += 1
            except Exception:
                db.rollback()
                LOGGER.exception("Realtime simulator scenario failed drain_id=%s", drain.id)
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


def _scenario_sequence(count: int) -> list[ScenarioProfile]:
    scenarios = list(SCENARIO_PROFILES)
    sequence: list[ScenarioProfile] = []
    while len(sequence) < count:
        _rng.shuffle(scenarios)
        sequence.extend(scenarios)
    return sequence[:count]


def _create_simulated_scenario_results(
    db: Session,
    drain: Drain,
    scenario: ScenarioProfile,
) -> list[dict[str, object]]:
    measured_at = datetime.now(timezone.utc)
    sensor_data = SensorData(
        drain_id=drain.id,
        water_level_cm=_random_range(scenario.water_level_range),
        flow_velocity_mps=_random_range(scenario.flow_velocity_range),
        measured_at=measured_at,
    )
    db.add(sensor_data)
    db.flush()

    yolo_result = YoloResult(
        drain_id=drain.id,
        image_url=_scenario_image_url(scenario.risk_level),
        obstruction_ratio=_random_range(scenario.obstruction_ratio_range),
        confidence_score=_random_range(scenario.confidence_score_range),
        yolo_status=scenario.yolo_status,
        captured_at=measured_at,
    )
    db.add(yolo_result)
    db.flush()

    xgboost_result = XgboostResult(
        drain_id=drain.id,
        sensor_data_id=sensor_data.id,
        yolo_result_id=yolo_result.id,
        risk_score=_random_range(scenario.risk_score_range),
        risk_level=scenario.risk_level,
        final_decision=scenario.final_decision,
        evaluated_at=measured_at,
    )
    db.add(xgboost_result)
    drain.status = scenario.risk_level
    db.commit()
    db.refresh(sensor_data)
    db.refresh(yolo_result)
    db.refresh(xgboost_result)
    db.refresh(drain)

    return [
        _yolo_result_event_payload(drain, yolo_result),
        _xgboost_result_event_payload(drain, xgboost_result),
        drain_status_event_payload(db, drain, xgboost_result, sensor_data=sensor_data, yolo_result=yolo_result),
    ]


def _scenario_image_url(risk_level: str) -> str | None:
    scenario_dir = SCENARIO_IMAGE_ROOT_DIR / risk_level
    if not scenario_dir.is_dir():
        return None

    image_paths = [
        path
        for path in scenario_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
    ]
    if not image_paths:
        return None

    image_path = _rng.choice(image_paths)
    return f"{MOCK_IMAGE_URL_PREFIX}/scenarios/{risk_level}/{quote(image_path.name)}"


def _yolo_result_event_payload(drain: Drain, yolo_result: YoloResult) -> dict[str, object]:
    return {
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


def _xgboost_result_event_payload(drain: Drain, result: XgboostResult) -> dict[str, object]:
    return {
        "type": XGBOOST_RESULT_UPDATED,
        "payload": {
            "drainId": drain.drain_code,
            "xgboostResultId": result.id,
            "sensorDataId": result.sensor_data_id,
            "yoloResultId": result.yolo_result_id,
            "riskLevel": result.risk_level,
            "riskScore": result.risk_score,
            "finalDecision": result.final_decision,
            "evaluatedAt": format_datetime(result.evaluated_at),
            "updatedAt": format_datetime(result.evaluated_at),
        },
    }


def _random_range(value_range: tuple[float, float]) -> float:
    return round(_rng.uniform(value_range[0], value_range[1]), 3)
