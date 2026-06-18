from datetime import datetime

from flood_risk_xgb.domain import DataQuality, StateCode, YoloResult
from flood_risk_xgb.features.schema import FeatureVector
from flood_risk_xgb.policy.quality_gate import QualityGate


def _features(**overrides: float) -> FeatureVector:
    base = {
        "obstruction_ratio": 0.1,
        "confidence_score": 0.1,
        "obstruction_mean_30m": 0.1,
        "obstruction_delta_30m": 0.0,
        "obstruction_persistence_count_30m": 0.0,
        "water_level_latest": 95,
        "flow_velocity_latest": 0.0,
        "water_level_mean_5m": 90,
        "flow_velocity_mean_5m": 0.05,
        "water_level_delta_5m": 10,
        "flow_velocity_delta_5m": -0.05,
        "water_level_mean_30m": 70,
        "flow_velocity_mean_30m": 0.2,
        "water_level_delta_30m": 45,
        "flow_velocity_delta_30m": -0.3,
        "water_level_slope_30m": 45 / 30,
        "flow_velocity_slope_30m": -0.3 / 30,
        "water_level_max_30m": 95,
        "flow_velocity_min_30m": 0.0,
        "water_level_std_30m": 12,
        "flow_velocity_std_30m": 0.08,
        "sensor_age_seconds": 30,
        "sensor_count_30m": 31,
        "sensor_valid_ratio_30m": 1.0,
    }
    base.update(overrides)
    return FeatureVector(**base)


def _yolo(confidence: float = 0.1, status: str = "unknown") -> YoloResult:
    return YoloResult(
        yolo_result_id=1,
        drain_id=101,
        captured_at=datetime.fromisoformat("2026-06-18T14:30:00+09:00"),
        image_uri="mock://image.jpg",
        obstruction_ratio=0.1,
        confidence_score=confidence,
        yolo_status=status,
    )


def test_low_yolo_confidence_can_be_overridden_by_clear_sensor_danger() -> None:
    gate = QualityGate(300, 3, 0.15, allow_sensor_danger_override=True)
    result = gate.evaluate(_yolo(), _features())
    assert result.can_predict is True
    assert result.warnings


def test_low_yolo_confidence_without_clear_sensor_danger_returns_unknown() -> None:
    gate = QualityGate(300, 3, 0.15, allow_sensor_danger_override=True)
    result = gate.evaluate(
        _yolo(),
        _features(
            water_level_latest=20,
            water_level_delta_5m=0,
            water_level_delta_30m=0,
            water_level_slope_30m=0,
            flow_velocity_latest=0.8,
        ),
    )
    assert result.can_predict is False
    assert result.state_code == StateCode.LOW_CONFIDENCE_VISION


def test_stale_sensor_is_rejected() -> None:
    gate = QualityGate(300, 3, 0.15)
    result = gate.evaluate(_yolo(confidence=0.9, status="good"), _features(sensor_age_seconds=301))
    assert result.can_predict is False
    assert result.data_quality == DataQuality.STALE
    assert "stale" in result.reason.lower()
