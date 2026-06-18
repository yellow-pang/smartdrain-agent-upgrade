"""Map model outcomes to public decision codes and concise explanations."""

from __future__ import annotations

from flood_risk_xgb.domain import DataQuality, FinalDecision, RiskLevel, StateCode
from flood_risk_xgb.features.schema import FeatureVector


FIELD_CHECK_STATES = {
    StateCode.INTERNAL_OR_DOWNSTREAM_OBSTRUCTION_SUSPECTED,
    StateCode.SENSOR_DETECTED_HIDDEN_RISK,
    StateCode.HIGH_INFLOW_WITH_SURFACE_OBSTRUCTION,
    StateCode.WATER_LEVEL_SPIKE,
    StateCode.FLOW_SENSOR_STUCK,
    StateCode.SENSOR_OSCILLATION,
    StateCode.VISION_SENSOR_CONFLICT,
    StateCode.INSUFFICIENT_SENSOR_HISTORY,
    StateCode.LOW_CONFIDENCE_VISION,
}

DISPATCH_STATES = {
    StateCode.SEVERE_OBSTRUCTION,
    StateCode.COMBINED_OBSTRUCTION,
    StateCode.PROGRESSIVE_OBSTRUCTION,
}


def final_decision_for(
    risk_level: RiskLevel,
    state_code: StateCode | None = None,
    data_quality: DataQuality = DataQuality.VALID,
) -> FinalDecision:
    if data_quality in {DataQuality.STALE, DataQuality.INVALID, DataQuality.INSUFFICIENT}:
        return FinalDecision.REVIEW_REQUIRED

    if state_code in DISPATCH_STATES:
        return FinalDecision.DISPATCH_REQUIRED
    if state_code in FIELD_CHECK_STATES:
        return FinalDecision.FIELD_CHECK

    if risk_level == RiskLevel.DANGER:
        return FinalDecision.DISPATCH_REQUIRED
    if risk_level == RiskLevel.CAUTION:
        return FinalDecision.MONITORING
    if risk_level == RiskLevel.GOOD:
        return FinalDecision.NORMAL
    return FinalDecision.REVIEW_REQUIRED


def build_decision_reason(
    risk_level: RiskLevel,
    features: FeatureVector | None,
    state_code: StateCode | None = None,
    reason_codes: list[str] | None = None,
) -> str:
    if risk_level == RiskLevel.UNKNOWN or features is None:
        return "Input quality was insufficient for a reliable XGBoost prediction."

    signals: list[str] = []
    if features.obstruction_ratio >= 0.65:
        signals.append("high obstruction ratio")
    elif features.obstruction_ratio >= 0.35:
        signals.append("moderate obstruction ratio")

    if features.obstruction_delta_30m >= 0.18:
        signals.append("increasing visual obstruction trend")

    if features.water_level_latest >= 80:
        signals.append("very high current water level")
    elif features.water_level_latest >= 45:
        signals.append("elevated current water level")

    if features.water_level_delta_30m >= 20:
        signals.append("rapid 30-minute water-level rise")
    elif features.water_level_delta_30m >= 8:
        signals.append("rising 30-minute water-level trend")
    elif features.water_level_delta_30m <= -8:
        signals.append("falling water-level trend")

    if features.flow_velocity_latest <= 0.12 and features.water_level_latest >= 30:
        signals.append("low flow velocity under elevated water level")
    elif features.flow_velocity_latest >= 0.60:
        signals.append("high current flow velocity")

    if not signals:
        signals.append("stable combined vision and sensor features")

    state_text = f"; state={state_code.value}" if state_code else ""
    reason_code_text = ""
    if reason_codes:
        reason_code_text = "; reasons=" + ",".join(reason_codes[:6])
    return (
        f"Model classified the record as {risk_level.value}{state_text} based on "
        + ", ".join(signals)
        + reason_code_text
        + "."
    )
