"""
하수구 위험도 예측 로직을 제공하는 파일입니다.

주요 역할:
- 막힘 비율, 신뢰도, 수위, 유속 값을 기반으로 위험 점수 계산
- 신뢰도와 임계값에 따른 위험 등급 반환
"""

def predict_risk(
    obstruction_ratio: float,
    confidence_score: float,
    water_level_cm: float,
    flow_velocity_mps: float,
) -> dict[str, float | str]:
    """Temporary rule-based predictor. Later, load xgboost_model.pkl here."""
    if confidence_score < 0.5:
        return {"risk_score": 0.0, "risk_level": "unknown"}

    water_score = min(max(water_level_cm / 100.0, 0.0), 1.0)
    velocity_score = min(max(flow_velocity_mps / 5.0, 0.0), 1.0)
    risk_score = round((obstruction_ratio * 0.5) + (water_score * 0.4) + (velocity_score * 0.1), 3)

    if obstruction_ratio >= 0.8 and water_level_cm >= 70:
        risk_level = "danger"
    elif obstruction_ratio >= 0.6 or water_level_cm >= 50:
        risk_level = "caution"
    else:
        risk_level = "good"

    return {"risk_score": risk_score, "risk_level": risk_level}
