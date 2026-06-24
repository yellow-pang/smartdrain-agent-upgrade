"""
SmartDrain 백엔드 연동 테스트용 mock AI 서버입니다.

실행 예:
uvicorn mock_ai_server.main:app --reload --port 9000
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import os
from typing import Any

import httpx
from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel, Field


app = FastAPI(title="SmartDrain Mock AI Server")


class SensorDataPayload(BaseModel):
    measured_at: str | None = None
    water_level_cm: float
    flow_velocity_mps: float
    quality_status: str = "valid"


class AnalysisRunRequest(BaseModel):
    request_id: str
    drain_id: int
    sensor_data: SensorDataPayload
    callback_url: str | None = None


class AnalysisRunResponse(BaseModel):
    accepted: bool = True
    request_id: str
    job_id: str
    status: str = "processing"
    message: str = "Mock AI analysis accepted"


@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "mock-ai-server"}


@app.post("/ai/analysis/run", response_model=AnalysisRunResponse)
async def run_analysis(payload: AnalysisRunRequest, background_tasks: BackgroundTasks) -> AnalysisRunResponse:
    job_id = f"AI_JOB_{payload.request_id}"
    callback_base_url = _resolve_callback_base_url(payload)
    background_tasks.add_task(_send_mock_callbacks, callback_base_url, payload, job_id)
    return AnalysisRunResponse(request_id=payload.request_id, job_id=job_id)


def _resolve_callback_base_url(payload: AnalysisRunRequest) -> str:
    if payload.callback_url:
        return payload.callback_url.rstrip("/")
    return os.getenv("AI_CALLBACK_BASE_URL", "http://localhost:8000").rstrip("/")


async def _send_mock_callbacks(callback_base_url: str, payload: AnalysisRunRequest, job_id: str) -> None:
    # 백엔드가 analysis_jobs row를 commit할 시간을 조금 둡니다.
    await asyncio.sleep(0.8)

    yolo_result = _mock_yolo_result(payload.sensor_data)
    xgboost_result = _mock_xgboost_result(payload.sensor_data, yolo_result)

    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            f"{callback_base_url}/api/ai-callback/yolo-result",
            json={
                "request_id": payload.request_id,
                "job_id": job_id,
                "yolo_result": yolo_result,
            },
        )

        await asyncio.sleep(0.3)

        await client.post(
            f"{callback_base_url}/api/ai-callback/xgboost-result",
            json={
                "request_id": payload.request_id,
                "job_id": job_id,
                "xgboost_result": xgboost_result,
            },
        )


def _mock_yolo_result(sensor_data: SensorDataPayload) -> dict[str, Any]:
    if sensor_data.quality_status != "valid":
        return {
            "obstruction_ratio": 0.0,
            "confidence_score": 0.3,
            "yolo_status": "good",
        }

    if sensor_data.water_level_cm >= 70:
        return {
            "obstruction_ratio": 0.88,
            "confidence_score": 0.94,
            "yolo_status": "blocked",
        }

    if sensor_data.water_level_cm >= 45:
        return {
            "obstruction_ratio": 0.62,
            "confidence_score": 0.89,
            "yolo_status": "dirty",
        }

    return {
        "obstruction_ratio": 0.18,
        "confidence_score": 0.93,
        "yolo_status": "good",
    }


def _mock_xgboost_result(sensor_data: SensorDataPayload, yolo_result: dict[str, Any]) -> dict[str, Any]:
    obstruction_ratio = float(yolo_result["obstruction_ratio"])
    water_level_cm = sensor_data.water_level_cm

    if float(yolo_result["confidence_score"]) < 0.5:
        risk_score = 0.0
        risk_level = "unknown"
        final_decision = "monitoring"
    elif obstruction_ratio >= 0.8 and water_level_cm >= 70:
        risk_score = 0.91
        risk_level = "danger"
        final_decision = "dispatch_required"
    elif obstruction_ratio >= 0.6 or water_level_cm >= 50:
        risk_score = 0.62
        risk_level = "caution"
        final_decision = "field_check"
    else:
        risk_score = 0.18
        risk_level = "good"
        final_decision = "normal"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "final_decision": final_decision,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }
