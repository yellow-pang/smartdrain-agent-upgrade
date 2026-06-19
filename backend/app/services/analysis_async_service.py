"""
AI 서버 비동기 분석 요청과 callback 저장을 처리하는 서비스 파일입니다.

주요 역할:
- 최신 센서 데이터를 기반으로 AI 분석 job 시작
- YOLO callback 결과 저장 및 분석 job 상태 갱신
- XGBoost callback 결과 저장, 하수구 상태 갱신, WebSocket payload 생성
"""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.analysis_job import AnalysisJob
from app.models.drain import Drain
from app.models.sensor_data import SensorData
from app.models.xgboost_result import XgboostResult
from app.models.yolo_result import YoloResult
from app.schemas.ai_callback import AiXgboostCallbackRequest, AiYoloCallbackRequest
from app.schemas.analysis_async import AnalysisAsyncRunRequest
from app.schemas.api_response import drain_status_event_payload, format_datetime, sensor_summary_dto
from app.services.ai_client import request_ai_analysis
from app.services.drain_service import get_drain_by_identifier

RISK_LEVELS = {"good", "caution", "danger", "unknown"}
FINAL_DECISIONS = {"normal", "monitoring", "field_check", "dispatch_required"}


async def start_async_analysis(db: Session, payload: AnalysisAsyncRunRequest) -> dict[str, object]:
    drain = get_drain_by_identifier(db, payload.drain_id)
    sensor_data = _get_latest_sensor_data(db, drain.id)
    if sensor_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor data not found")

    request_id = _create_request_id(drain.id)
    ai_payload = {
        "request_id": request_id,
        "drain_id": drain.id,
        "sensor_data": {
            "measured_at": format_datetime(sensor_data.measured_at),
            "water_level_cm": sensor_data.water_level_cm,
            "flow_velocity_mps": sensor_data.flow_velocity_mps,
            # TODO: SensorData 모델에 quality_status가 추가되면 실제 값을 전달합니다.
            "quality_status": "valid",
        },
    }
    ai_response = await request_ai_analysis(ai_payload)

    job = AnalysisJob(
        request_id=request_id,
        job_id=ai_response.job_id,
        drain_id=drain.id,
        sensor_data_id=sensor_data.id,
        sensor_measured_at=sensor_data.measured_at,
        status=ai_response.status or "processing",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return {
        "requestId": job.request_id,
        "jobId": job.job_id,
        "drainId": drain.drain_code,
        "status": job.status,
        "sensorSummary": sensor_summary_dto(sensor_data),
    }


def save_yolo_callback(db: Session, payload: AiYoloCallbackRequest) -> YoloResult:
    job = _get_analysis_job(db, payload.request_id, payload.job_id)
    yolo_payload = payload.yolo_result
    yolo_result = YoloResult(
        drain_id=job.drain_id,
        image_url=f"ai-server://mock/{job.drain_id}",
        obstruction_ratio=_normalize_obstruction_ratio(yolo_payload.obstruction_ratio),
        confidence_score=yolo_payload.confidence_score,
        yolo_status=_normalize_callback_yolo_status(yolo_payload.yolo_status),
        captured_at=datetime.now(timezone.utc),
    )
    db.add(yolo_result)
    db.flush()

    job.yolo_result_id = yolo_result.id
    job.status = "yolo_completed"
    job.error_message = None
    db.commit()
    db.refresh(yolo_result)
    return yolo_result


def save_xgboost_callback(db: Session, payload: AiXgboostCallbackRequest) -> tuple[XgboostResult, dict[str, object]]:
    job = _get_analysis_job(db, payload.request_id, payload.job_id)
    if job.yolo_result_id is None:
        job.status = "xgboost_received_without_yolo"
        job.error_message = "XGBoost callback received before YOLO callback"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="YOLO result not found",
        )

    xgboost_payload = payload.xgboost_result
    risk_level = _normalize_risk_level(xgboost_payload.risk_level)
    final_decision = _normalize_final_decision(xgboost_payload.final_decision)
    evaluated_at = _ensure_timezone(xgboost_payload.evaluated_at)

    result = XgboostResult(
        drain_id=job.drain_id,
        sensor_data_id=job.sensor_data_id,
        yolo_result_id=job.yolo_result_id,
        risk_score=xgboost_payload.risk_score,
        risk_level=risk_level,
        final_decision=final_decision,
        evaluated_at=evaluated_at,
    )
    drain = db.get(Drain, job.drain_id)
    if drain is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drain not found")
    drain.status = risk_level

    job.status = "completed"
    job.error_message = None
    db.add(result)
    db.commit()
    db.refresh(result)

    event = drain_status_event_payload(
        db,
        drain,
        result,
        sensor_data=job.sensor_data,
        yolo_result=job.yolo_result,
    )
    return result, event


def _get_latest_sensor_data(db: Session, drain_id: int) -> SensorData | None:
    # TODO: SensorData 모델에 quality_status가 추가되면 quality_status="valid"를 우선 조회합니다.
    return (
        db.query(SensorData)
        .filter(SensorData.drain_id == drain_id)
        .order_by(SensorData.measured_at.desc())
        .first()
    )


def _get_analysis_job(db: Session, request_id: str, job_id: str | None) -> AnalysisJob:
    filters = [AnalysisJob.request_id == request_id]
    if job_id:
        filters.append(AnalysisJob.job_id == job_id)
    job = db.query(AnalysisJob).filter(or_(*filters)).order_by(AnalysisJob.created_at.desc()).first()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis request not found")
    return job


def _create_request_id(drain_id: int) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    return f"REQ_{timestamp}_{drain_id}"


def _normalize_obstruction_ratio(value: float) -> float:
    return value / 100 if value > 1 else value


def _normalize_callback_yolo_status(value: str) -> str:
    return {
        "good": "clear",
        "dirty": "partially_blocked",
        "blocked": "blocked",
    }.get(value, value if value in {"clear", "partially_blocked", "unknown"} else "unknown")


def _normalize_risk_level(value: str) -> str:
    return value if value in RISK_LEVELS else "unknown"


def _normalize_final_decision(value: str) -> str:
    return value if value in FINAL_DECISIONS else "monitoring"


def _ensure_timezone(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
