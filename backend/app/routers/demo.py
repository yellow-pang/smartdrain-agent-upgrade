from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.schemas.api_response import api_response
from app.services import demo_simulator

router = APIRouter(prefix="/api/demo", tags=["demo"])


class DemoPresetRequest(BaseModel):
    preset: str


class DemoScenarioStepRequest(BaseModel):
    weatherStep: str


class DemoScenarioIntervalRequest(BaseModel):
    intervalSeconds: int


def require_demo_access(
    authorization: str | None = Header(default=None),
    x_demo_control_token: str | None = Header(default=None),
) -> None:
    if not settings.DEMO_SIMULATOR_ENABLED:
        raise HTTPException(status_code=404, detail="Demo control is disabled")

    expected_token = (settings.DEMO_CONTROL_TOKEN or "").strip()
    if not expected_token:
        raise HTTPException(status_code=403, detail="Demo control token is not configured")

    bearer_token = ""
    if authorization and authorization.lower().startswith("bearer "):
        bearer_token = authorization[7:].strip()

    if x_demo_control_token == expected_token or bearer_token == expected_token:
        return

    raise HTTPException(status_code=401, detail="Invalid demo control token")


@router.get("/status")
async def demo_status(_: None = Depends(require_demo_access)):
    return api_response(await demo_simulator.get_demo_status())


@router.post("/drains/{drain_id}/preset")
async def apply_drain_preset(
    drain_id: str,
    payload: DemoPresetRequest,
    _: None = Depends(require_demo_access),
    db: Session = Depends(get_db),
):
    try:
        status = await demo_simulator.apply_manual_preset(db, drain_id, payload.preset)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return api_response(status, message="Demo preset applied")


@router.delete("/drains/{drain_id}/override")
async def clear_drain_override(
    drain_id: str,
    _: None = Depends(require_demo_access),
):
    return api_response(
        await demo_simulator.clear_manual_override(drain_id),
        message="Demo override cleared",
    )


@router.post("/reset")
async def reset_demo(
    _: None = Depends(require_demo_access),
    db: Session = Depends(get_db),
):
    return api_response(await demo_simulator.reset_demo(db), message="Demo reset")


@router.post("/scenario/start")
async def start_demo_scenario(_: None = Depends(require_demo_access)):
    return api_response(
        await demo_simulator.start_controlled_scenario(),
        message="Demo scenario started",
    )


@router.post("/scenario/pause")
async def pause_demo_scenario(_: None = Depends(require_demo_access)):
    return api_response(
        await demo_simulator.pause_controlled_scenario(),
        message="Demo scenario paused",
    )


@router.post("/scenario/resume")
async def resume_demo_scenario(_: None = Depends(require_demo_access)):
    return api_response(
        await demo_simulator.resume_controlled_scenario(),
        message="Demo scenario resumed",
    )


@router.post("/scenario/stop")
async def stop_demo_scenario(_: None = Depends(require_demo_access)):
    return api_response(
        await demo_simulator.stop_controlled_scenario(),
        message="Demo scenario stopped",
    )


@router.post("/scenario/next")
async def next_demo_scenario_step(
    _: None = Depends(require_demo_access),
    db: Session = Depends(get_db),
):
    return api_response(
        await demo_simulator.next_scenario_step(db),
        message="Demo scenario advanced",
    )


@router.post("/scenario/step")
async def apply_demo_scenario_step(
    payload: DemoScenarioStepRequest,
    _: None = Depends(require_demo_access),
    db: Session = Depends(get_db),
):
    try:
        status = await demo_simulator.apply_scenario_step(db, payload.weatherStep)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return api_response(status, message="Demo scenario step applied")


@router.post("/scenario/interval")
async def set_demo_scenario_interval(
    payload: DemoScenarioIntervalRequest,
    _: None = Depends(require_demo_access),
):
    try:
        status = await demo_simulator.set_scenario_interval(payload.intervalSeconds)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return api_response(status, message="Demo scenario interval updated")


@router.post("/scenario/recover")
async def recover_demo_scenario(
    _: None = Depends(require_demo_access),
    db: Session = Depends(get_db),
):
    return api_response(
        await demo_simulator.recover_demo(db),
        message="Demo scenario recovered",
    )


@router.post("/scenario/reset")
async def reset_demo_scenario(
    _: None = Depends(require_demo_access),
    db: Session = Depends(get_db),
):
    return api_response(await demo_simulator.reset_demo(db), message="Demo scenario reset")
