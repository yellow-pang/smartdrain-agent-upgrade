from datetime import datetime, timedelta, timezone

from ai_service._yolo.fake_yolo_predictor import FakeYoloPredictor
from ai_service.xgboost.service import predict_flood_risk_batch

from .callback_payloads import (
    build_accepted_response,
    build_xgboost_callback_payload,
    build_yolo_callback_payload,
)
from .job_id import build_job_id
from .validator import validate_analysis_request
from .xgboost_adapter import build_xgboost_input_batch

KST = timezone(timedelta(hours=9))


def run_analysis_job(payload: dict) -> dict:
    validate_analysis_request(payload)

    request_id = payload["request_id"]
    drain_id = payload["drain_id"]
    sensor_data = payload["sensor_data"]
    job_id = build_job_id(request_id)

    yolo_result = FakeYoloPredictor().predict(drain_id)
    xgboost_input_batch = build_xgboost_input_batch(sensor_data, yolo_result)
    xgboost_result = predict_flood_risk_batch(xgboost_input_batch)[0]

    return {
        "accepted_response": build_accepted_response(request_id, job_id),
        "yolo_callback_payload": build_yolo_callback_payload(
            request_id,
            job_id,
            yolo_result,
        ),
        "xgboost_callback_payload": build_xgboost_callback_payload(
            request_id,
            job_id,
            xgboost_result,
            _evaluated_at_now(),
        ),
    }


def _evaluated_at_now() -> str:
    return datetime.now(KST).isoformat()
