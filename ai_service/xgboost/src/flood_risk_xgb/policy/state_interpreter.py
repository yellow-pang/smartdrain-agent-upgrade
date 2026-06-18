"""Translate XGBoost output and feature patterns into domain state codes."""

from __future__ import annotations

from dataclasses import dataclass, field

from flood_risk_xgb.domain import DataQuality, RiskLevel, StateCode
from flood_risk_xgb.features.schema import FeatureVector


@dataclass(frozen=True)
class StateInterpretation:
    state_code: StateCode
    reason_codes: list[str] = field(default_factory=list)
    decision_reason: str = ""


def _base_reason_codes(features: FeatureVector) -> list[str]:
    reason_codes: list[str] = []
    if features.obstruction_ratio >= 0.65:
        reason_codes.append("YOLO_OBSTRUCTION_HIGH")
    elif features.obstruction_ratio >= 0.35:
        reason_codes.append("YOLO_OBSTRUCTION_MODERATE")

    if features.water_level_latest >= 80:
        reason_codes.append("WATER_LEVEL_VERY_HIGH")
    elif features.water_level_latest >= 45:
        reason_codes.append("WATER_LEVEL_ELEVATED")

    if features.water_level_delta_30m >= 20 or features.water_level_slope_30m >= 0.70:
        reason_codes.append("WATER_LEVEL_RISING_FAST")
    elif features.water_level_delta_30m >= 8:
        reason_codes.append("WATER_LEVEL_RISING")
    elif features.water_level_delta_30m <= -8:
        reason_codes.append("WATER_LEVEL_FALLING")

    if features.flow_velocity_latest <= 0.15:
        reason_codes.append("FLOW_VELOCITY_LOW")
    elif features.flow_velocity_latest >= 0.60:
        reason_codes.append("FLOW_VELOCITY_FAST")

    if features.flow_velocity_delta_30m <= -0.20:
        reason_codes.append("FLOW_VELOCITY_DECLINING")
    elif features.flow_velocity_delta_30m >= 0.15:
        reason_codes.append("FLOW_VELOCITY_RECOVERING")

    if features.obstruction_delta_30m >= 0.18:
        reason_codes.append("YOLO_OBSTRUCTION_INCREASING")
    if features.obstruction_persistence_count_30m >= 3:
        reason_codes.append("YOLO_OBSTRUCTION_PERSISTENT")
    return reason_codes


def interpret_state(
    risk_level: RiskLevel,
    features: FeatureVector | None,
    data_quality: DataQuality,
    preselected_state: StateCode | None = None,
    preselected_reason_codes: list[str] | None = None,
) -> StateInterpretation:
    if preselected_state is not None:
        codes = list(preselected_reason_codes or [])
        reason = f"Analysis state selected by data quality gate: {preselected_state.value}."
        return StateInterpretation(preselected_state, codes, reason)

    if features is None:
        return StateInterpretation(
            StateCode.UNKNOWN_STATE,
            list(preselected_reason_codes or ["FEATURES_UNAVAILABLE"]),
            "Feature vector was unavailable, so detailed state interpretation was skipped.",
        )

    reason_codes = _base_reason_codes(features)
    obstruction_high = features.obstruction_ratio >= 0.65
    obstruction_moderate = features.obstruction_ratio >= 0.35
    obstruction_low = features.obstruction_ratio < 0.35
    water_low = features.water_level_latest < 25
    water_elevated = features.water_level_latest >= 45
    water_high = features.water_level_latest >= 80
    water_near_capacity = features.water_level_latest >= 70
    water_rising = features.water_level_delta_30m >= 8 or features.water_level_slope_30m >= 0.30
    water_rising_fast = features.water_level_delta_30m >= 20 or features.water_level_slope_30m >= 0.70
    water_stable = abs(features.water_level_delta_30m) < 4
    water_falling = features.water_level_delta_30m <= -8
    flow_low = features.flow_velocity_latest <= 0.15
    flow_slowish = features.flow_velocity_latest <= 0.30
    flow_fast = features.flow_velocity_latest >= 0.60
    flow_declining = features.flow_velocity_delta_30m <= -0.20
    flow_recovering = features.flow_velocity_delta_30m >= 0.15
    obstruction_increasing = features.obstruction_delta_30m >= 0.25
    obstruction_persistent = features.obstruction_persistence_count_30m >= 3

    if data_quality in {DataQuality.SUSPECT, DataQuality.STALE, DataQuality.INSUFFICIENT, DataQuality.INVALID}:
        reason_codes.append(f"DATA_QUALITY_{data_quality.value.upper()}")

    if obstruction_increasing and water_rising and flow_declining:
        state = StateCode.PROGRESSIVE_OBSTRUCTION
    elif obstruction_low and features.obstruction_ratio < 0.10 and risk_level == RiskLevel.DANGER:
        state = StateCode.SENSOR_DETECTED_HIDDEN_RISK
    elif obstruction_moderate and not obstruction_persistent and features.water_level_std_30m >= 3.0 and features.flow_velocity_std_30m >= 0.035:
        state = StateCode.INTERMITTENT_OBSTRUCTION
    elif obstruction_high and water_high and flow_low and water_rising:
        state = StateCode.SEVERE_OBSTRUCTION
    elif obstruction_high and water_elevated and (flow_slowish or flow_declining) and water_rising:
        state = StateCode.COMBINED_OBSTRUCTION
    elif obstruction_low and water_elevated and water_rising and (flow_slowish or flow_declining):
        state = StateCode.INTERNAL_OR_DOWNSTREAM_OBSTRUCTION_SUSPECTED
    elif obstruction_low and water_elevated and water_rising and flow_fast:
        state = StateCode.HYDRAULIC_OVERLOAD
    elif obstruction_high and water_rising and flow_fast:
        state = StateCode.HIGH_INFLOW_WITH_SURFACE_OBSTRUCTION
    elif water_elevated and water_falling and flow_recovering:
        state = StateCode.RECOVERING
    elif water_near_capacity and water_stable and flow_fast:
        state = StateCode.NEAR_CAPACITY_STABLE
    elif obstruction_high and water_low and flow_slowish and water_stable:
        state = StateCode.DRY_SURFACE_OBSTRUCTION
    elif obstruction_high and water_falling and flow_fast:
        state = StateCode.DRAINING_WITH_SURFACE_OBSTRUCTION
    elif obstruction_high and water_low and (flow_fast or not flow_slowish):
        state = StateCode.SURFACE_OBSTRUCTION_LIKELY
    elif obstruction_high and water_stable and flow_fast:
        state = StateCode.SURFACE_OBSTRUCTION_LIKELY
    elif obstruction_high and water_stable and features.confidence_score < 0.45:
        state = StateCode.VISION_SENSOR_CONFLICT
    elif obstruction_moderate and water_rising_fast and not flow_declining:
        state = StateCode.HYDRAULIC_OVERLOAD
    elif risk_level == RiskLevel.UNKNOWN:
        state = StateCode.UNKNOWN_STATE
    else:
        state = StateCode.NORMAL_DRAINAGE

    if state in {
        StateCode.SEVERE_OBSTRUCTION,
        StateCode.COMBINED_OBSTRUCTION,
        StateCode.INTERNAL_OR_DOWNSTREAM_OBSTRUCTION_SUSPECTED,
        StateCode.SENSOR_DETECTED_HIDDEN_RISK,
    }:
        reason_codes.append("DRAINAGE_CAPACITY_DEGRADED")
    if state == StateCode.SURFACE_OBSTRUCTION_LIKELY:
        reason_codes.append("SURFACE_BLOCKED_BUT_FLOW_AVAILABLE")
    if state == StateCode.HYDRAULIC_OVERLOAD:
        reason_codes.append("HIGH_INFLOW_SUSPECTED")
    if obstruction_persistent:
        reason_codes.append("PERSISTENT_VISUAL_OBSTRUCTION")

    unique_codes = list(dict.fromkeys(reason_codes))
    reason = f"State interpreted as {state.value} from risk={risk_level.value} and feature pattern."
    return StateInterpretation(state, unique_codes, reason)
