BACKEND_FINAL_DECISION_BY_RISK_LEVEL = {
    "good": "normal",
    "caution": "monitoring",
    "danger": "dispatch_required",
    "unknown": "field_check",
}


def map_risk_level_to_backend_decision(risk_level: str) -> str:
    try:
        return BACKEND_FINAL_DECISION_BY_RISK_LEVEL[risk_level]
    except KeyError as exc:
        raise ValueError(f"Unsupported risk_level: {risk_level}") from exc

