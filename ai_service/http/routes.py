import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from ai_service.analysis.callback_payloads import build_accepted_response
from ai_service.analysis.job_id import build_job_id
from ai_service.analysis.service import run_analysis_job
from ai_service.analysis.validator import validate_analysis_request

from .callback_sender import send_json_callback
from .config import get_http_settings

LOGGER = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ai/analysis/run")
def run_analysis(payload: dict, background_tasks: BackgroundTasks) -> dict:
    try:
        validate_analysis_request(payload)
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
    try:
        result = run_analysis_job(payload)
    except Exception:
        LOGGER.exception("AI analysis background task failed.")
        return

    settings = get_http_settings()
    send_json_callback(
        settings.yolo_callback_url,
        result["yolo_callback_payload"],
        settings.callback_timeout_seconds,
        settings.callback_retry_count,
    )
    send_json_callback(
        settings.xgboost_callback_url,
        result["xgboost_callback_payload"],
        settings.callback_timeout_seconds,
        settings.callback_retry_count,
    )
