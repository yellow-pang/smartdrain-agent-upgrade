"""
AI 서버 비동기 분석 요청과 callback 저장을 처리하는 서비스 파일입니다.

주요 역할:
- 최신 센서 데이터를 기반으로 AI 분석 job 시작
- YOLO callback 결과 저장 및 분석 job 상태 갱신
- XGBoost callback 결과 저장, 하수구 상태 갱신, WebSocket payload 생성
"""

from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
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
from app.websocket.events import DRAIN_STATUS_UPDATED, XGBOOST_RESULT_UPDATED, YOLO_RESULT_UPDATED

RISK_LEVELS = {"good", "caution", "danger", "unknown"}
FINAL_DECISIONS = {"normal", "monitoring", "field_check", "dispatch_required"}
MOCK_IMAGE_URL_PREFIX = "/api/mock-images"
PROJECT_ROOT_DIR = Path(__file__).resolve().parents[3]
MOCK_IMAGE_SOURCE_DIR = PROJECT_ROOT_DIR / "mock_data" / "ai_image_samples"


async def start_async_analysis(db: Session, payload: AnalysisAsyncRunRequest) -> dict[str, object]:
    drain = get_drain_by_identifier(db, payload.drain_id)
    return await start_analysis_for_drain(db, drain, trigger_type="manual")


async def start_analysis_for_drain(db: Session, drain: Drain, trigger_type: str = "manual") -> dict[str, object]:
    sensor_data = _get_latest_sensor_data(db, drain.id)
    if sensor_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor data not found")

    request_id = _create_request_id(drain.id)
    job_id = _create_job_id(request_id)
    job = AnalysisJob(
        request_id=request_id,
        job_id=job_id,
        drain_id=drain.id,
        sensor_data_id=sensor_data.id,
        sensor_measured_at=sensor_data.measured_at,
        status="processing",
        trigger_type=trigger_type,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    ai_payload = {
        "request_id": request_id,
        "job_id": job_id,
        "drain_id": drain.id,
        "callback_url": settings.AI_CALLBACK_BASE_URL,
        "sensor_data": {
            "measured_at": format_datetime(sensor_data.measured_at),
            "water_level_cm": sensor_data.water_level_cm,
            "flow_velocity_mps": sensor_data.flow_velocity_mps,
            # TODO: SensorData 모델에 quality_status가 추가되면 실제 값을 전달합니다.
            "quality_status": "valid",
        },
    }
    try:
        ai_response = await request_ai_analysis(ai_payload)
    except HTTPException as exc:
        job.status = "failed"
        job.error_message = str(exc.detail)
        db.commit()
        raise
    except Exception as exc:
        job.status = "failed"
        job.error_message = f"Unexpected analysis start error: {exc}"
        db.commit()
        raise

    if ai_response.job_id and ai_response.job_id != job_id:
        job.error_message = f"AI server returned different job_id: {ai_response.job_id}"
    if ai_response.status in {"processing", "yolo_completed", "completed", "failed"}:
        job.status = ai_response.status
    db.commit()
    db.refresh(job)

    return {
        "requestId": job.request_id,
        "jobId": job.job_id,
        "drainId": drain.drain_code,
        "status": job.status,
        "sensorSummary": sensor_summary_dto(sensor_data),
    }


def save_yolo_callback(db: Session, payload: AiYoloCallbackRequest) -> tuple[YoloResult, dict[str, object] | None]:
    job = _get_analysis_job(db, payload.request_id, payload.job_id)
    if job.yolo_result_id is not None:
        yolo_result = db.get(YoloResult, job.yolo_result_id)
        if yolo_result is not None:
            # Duplicate callbacks are idempotent. We intentionally do not rebroadcast WebSocket events.
            return yolo_result, None

    yolo_payload = payload.yolo_result
    yolo_result = YoloResult(
        drain_id=job.drain_id,
        image_url=_mock_image_url(job.drain_id),
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
    event = _yolo_result_event_payload(job, yolo_result)
    return yolo_result, event


def save_xgboost_callback(
    db: Session,
    payload: AiXgboostCallbackRequest,
) -> tuple[XgboostResult, dict[str, object] | None, dict[str, object] | None]:
    job = _get_analysis_job(db, payload.request_id, payload.job_id)
    existing_result = _get_existing_xgboost_result(db, job)
    if job.status == "completed" and existing_result is not None:
        # Duplicate callbacks are idempotent. We intentionally do not rebroadcast WebSocket events.
        return existing_result, None, None

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

    xgboost_event = xgboost_result_event_payload(job, result)
    drain_status_event = drain_status_event_payload(
        db,
        drain,
        result,
        sensor_data=job.sensor_data,
        yolo_result=job.yolo_result,
    )
    _extend_drain_status_event(drain_status_event, job, job.yolo_result)
    return result, xgboost_event, drain_status_event


def _yolo_result_event_payload(job: AnalysisJob, yolo_result: YoloResult) -> dict[str, object]:
    return {
        "type": YOLO_RESULT_UPDATED,
        "payload": {
            "drainId": job.drain.drain_code,
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


def xgboost_result_event_payload(job: AnalysisJob, result: XgboostResult) -> dict[str, object]:
    return {
        "type": XGBOOST_RESULT_UPDATED,
        "payload": {
            "drainId": job.drain.drain_code,
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


def _extend_drain_status_event(
    event: dict[str, object],
    job: AnalysisJob,
    yolo_result: YoloResult | None,
) -> None:
    payload = event["payload"]
    if not isinstance(payload, dict):
        return
    payload.update(
        {
            "sensorDataId": job.sensor_data_id,
            "yoloResultId": yolo_result.id if yolo_result else None,
            "xgboostResultId": payload.get("xgboostResultId"),
        }
    )
    event["type"] = DRAIN_STATUS_UPDATED


def _get_latest_sensor_data(db: Session, drain_id: int) -> SensorData | None:
    # TODO: SensorData 모델에 quality_status가 추가되면 quality_status="valid"를 우선 조회합니다.
    return (
        db.query(SensorData)
        .filter(SensorData.drain_id == drain_id)
        .order_by(SensorData.measured_at.desc())
        .first()
    )


def _get_existing_xgboost_result(db: Session, job: AnalysisJob) -> XgboostResult | None:
    if job.yolo_result_id is None:
        return None
    return (
        db.query(XgboostResult)
        .filter(
            XgboostResult.drain_id == job.drain_id,
            XgboostResult.sensor_data_id == job.sensor_data_id,
            XgboostResult.yolo_result_id == job.yolo_result_id,
        )
        .order_by(XgboostResult.created_at.desc())
        .first()
    )


def _get_analysis_job(db: Session, request_id: str, job_id: str | None) -> AnalysisJob:
    query = db.query(AnalysisJob).filter(AnalysisJob.request_id == request_id)
    if job_id:
        query = query.filter(AnalysisJob.job_id == job_id)
    job = query.order_by(AnalysisJob.created_at.desc()).first()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis request not found")
    return job


def _create_request_id(drain_id: int) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    return f"REQ_{timestamp}_{drain_id}"


def _create_job_id(request_id: str) -> str:
    return f"AI_JOB_{request_id}"


def _normalize_obstruction_ratio(value: float) -> float:
    return value / 100 if value > 1 else value


def _mock_image_url(drain_id: int) -> str | None:
    image_path = MOCK_IMAGE_SOURCE_DIR / f"drain_{drain_id}.jpg"
    if not image_path.is_file():
        return None
    return f"{MOCK_IMAGE_URL_PREFIX}/drain_{drain_id}.jpg"


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
