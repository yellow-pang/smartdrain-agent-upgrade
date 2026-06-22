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
        # source가 없는 drain_id는 분석 job을 accepted 하기 전에 거절한다.
        # 그래야 callback 없이 background task에서 조용히 실패하는 상황을 줄일 수 있다.
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
    try:
        result = run_analysis_job(payload)
    except Exception:
        # callback payload 계약에는 실패 전용 shape가 아직 없다.
        # 따라서 background 실패는 로그로 남기고 backend callback은 보내지 않는다.
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
