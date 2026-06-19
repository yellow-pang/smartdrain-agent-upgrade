from .decision_mapper import map_risk_level_to_backend_decision


def build_accepted_response(request_id: str, job_id: str) -> dict:
    return {
        "accepted": True,
        "request_id": request_id,
        "job_id": job_id,
        "status": "processing",
    }


def build_yolo_callback_payload(
    request_id: str,
    job_id: str,
    yolo_result: dict,
) -> dict:
    return {
        "request_id": request_id,
        "job_id": job_id,
        "yolo_result": yolo_result,
    }


def build_xgboost_callback_payload(
    request_id: str,
    job_id: str,
    xgboost_result: dict,
    evaluated_at: str,
) -> dict:
    risk_level = xgboost_result["risk_level"]
    return {
        "request_id": request_id,
        "job_id": job_id,
        "xgboost_result": {
            "risk_score": xgboost_result["risk_score"],
            "risk_level": risk_level,
            "final_decision": map_risk_level_to_backend_decision(risk_level),
            "evaluated_at": evaluated_at,
        },
    }

