"""
실시간 대시보드 자동 시뮬레이터 제어 API를 제공합니다.
"""

from fastapi import APIRouter

from app.schemas.api_response import api_response
from app.schemas.realtime_simulator import RealtimeSimulatorStartRequest
from app.services.realtime_simulator import (
    get_realtime_simulator_status,
    start_realtime_simulator,
    stop_realtime_simulator,
)

router = APIRouter(prefix="/api/realtime-simulator", tags=["realtime-simulator"])


@router.get("/status")
def get_realtime_simulator_runtime_status():
    return api_response(get_realtime_simulator_status())


@router.post("/start")
async def start_realtime_simulator_runtime(payload: RealtimeSimulatorStartRequest):
    status_payload, started_now = await start_realtime_simulator(payload.interval_seconds)
    message = "Realtime simulator started" if started_now else "Realtime simulator is already running"
    return api_response(status_payload, message=message)


@router.post("/stop")
async def stop_realtime_simulator_runtime():
    status_payload, stopped_now = await stop_realtime_simulator()
    message = "Realtime simulator stopped" if stopped_now else "Realtime simulator is already stopped"
    return api_response(status_payload, message=message)
