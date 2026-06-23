import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from ai_service.analysis.callback_payloads import build_accepted_response
from ai_service.analysis.job_id import build_job_id
from ai_service.analysis.service import run_analysis_job
from ai_service.analysis.validator import (
    validate_analysis_image_source,
    validate_analysis_request,
)

from .callback_sender import send_json_callback
from .config import get_http_settings

LOGGER = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ai/analysis/run")
def run_analysis(payload: dict, background_tasks: BackgroundTasks) -> dict:
    try:
        validate_analysis_request(payload)
        validate_analysis_image_source(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_INPUT",
                    "message": str(exc),
                    "detail": {},
                },
            },
        ) from exc

    request_id = payload["request_id"]
    job_id = build_job_id(request_id)
    background_tasks.add_task(process_analysis_callbacks, payload)
    return build_accepted_response(request_id, job_id)


def process_analysis_callbacks(payload: dict) -> None:
    request_id = payload.get("request_id")
    job_id = build_job_id(request_id) if request_id else None
    drain_id = payload.get("drain_id")

    try:
        result = run_analysis_job(payload)
    except Exception:
        LOGGER.exception(
            "AI analysis background task failed: request_id=%s job_id=%s drain_id=%s",
            request_id,
            job_id,
            drain_id,
        )
        return

    settings = get_http_settings()
    yolo_sent = send_json_callback(
        settings.yolo_callback_url,
        result["yolo_callback_payload"],
        settings.callback_timeout_seconds,
        settings.callback_retry_count,
        callback_name="yolo",
        request_id=request_id,
        job_id=job_id,
    )
    _log_callback_result("yolo", yolo_sent, request_id, job_id, drain_id)

    xgboost_sent = send_json_callback(
        settings.xgboost_callback_url,
        result["xgboost_callback_payload"],
        settings.callback_timeout_seconds,
        settings.callback_retry_count,
        callback_name="xgboost",
        request_id=request_id,
        job_id=job_id,
    )
    _log_callback_result("xgboost", xgboost_sent, request_id, job_id, drain_id)


def _log_callback_result(
    callback_name: str,
    sent: bool,
    request_id: str | None,
    job_id: str | None,
    drain_id: object,
) -> None:
    if sent:
        LOGGER.info(
            "AI callback delivered: callback=%s request_id=%s job_id=%s drain_id=%s",
            callback_name,
            request_id,
            job_id,
            drain_id,
        )
        return

    LOGGER.error(
        "AI callback delivery exhausted: callback=%s request_id=%s job_id=%s drain_id=%s",
        callback_name,
        request_id,
        job_id,
        drain_id,
    )
