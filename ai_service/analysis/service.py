from datetime import datetime, timedelta, timezone

from ai_service.image_source.service import resolve_image_source_by_drain_id
from ai_service.yolo.analyzer import predict_yolo_by_image_path
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

    # 백엔드는 image_path를 보내지 않는다. 운영 흐름에서는 drain_id로 이미지 소스를 찾고,
    # 그 결과 local_path만 YOLO에 넘겨 HTTP 계약과 모델 입력 책임을 분리한다.
    image_source = resolve_image_source_by_drain_id(drain_id)
    yolo_result = predict_yolo_by_image_path(image_source.local_path)

    # YOLO 출력과 센서값을 XGBoost 학습 feature 순서에 맞춰 변환하는 경계다.
    # 이 위치를 고정해 두면 YOLO/XGBoost 내부 구현이 바뀌어도 callback 계약은 유지된다.
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
