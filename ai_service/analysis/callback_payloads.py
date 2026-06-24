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
    # 백엔드 callback contract를 이 함수에 모아 두어 모델 내부 변경이
    # HTTP payload shape를 직접 흔들지 않도록 한다.
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
    # XGBoost의 risk_level과 백엔드 화면/업무 판단 코드는 분리되어 있다.
    # 이 mapping을 analysis 계층에서 수행해야 모델 계층이 backend 정책을 몰라도 된다.
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
