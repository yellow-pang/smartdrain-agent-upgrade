from datetime import datetime

import pytest

from flood_risk_xgb.domain import SensorRecord, YoloResult
from flood_risk_xgb.features.builder import FeatureBuilder


def test_feature_builder_excludes_future_and_non_valid_records() -> None:
    yolo = YoloResult(
        yolo_result_id=1,
        drain_id=101,
        captured_at=datetime.fromisoformat("2026-06-18T14:30:00+09:00"),
        image_uri="mock://image.jpg",
        obstruction_ratio=0.4,
        confidence_score=0.9,
        yolo_status="caution",
    )
    yolo_history = [
        YoloResult(
            yolo_result_id=91,
            drain_id=101,
            captured_at=datetime.fromisoformat("2026-06-18T14:10:00+09:00"),
            image_uri="mock://history.jpg",
            obstruction_ratio=0.2,
            confidence_score=0.8,
            yolo_status="good",
            analysis_target=False,
        )
    ]
    rows = [
        SensorRecord(
            measured_at=datetime.fromisoformat("2026-06-18T14:00:00+09:00"),
            drain_id=101,
            water_level_cm=10,
            flow_velocity_mps=0.8,
            quality_status="valid",
        ),
        SensorRecord(
            measured_at=datetime.fromisoformat("2026-06-18T14:25:00+09:00"),
            drain_id=101,
            water_level_cm=20,
            flow_velocity_mps=0.5,
            quality_status="valid",
        ),
        SensorRecord(
            measured_at=datetime.fromisoformat("2026-06-18T14:29:00+09:00"),
            drain_id=101,
            water_level_cm=30,
            flow_velocity_mps=0.2,
            quality_status="valid",
        ),
        SensorRecord(
            measured_at=datetime.fromisoformat("2026-06-18T14:30:00+09:00"),
            drain_id=101,
            water_level_cm=99,
            flow_velocity_mps=0.0,
            quality_status="suspect",
        ),
        SensorRecord(
            measured_at=datetime.fromisoformat("2026-06-18T14:31:00+09:00"),
            drain_id=101,
            water_level_cm=100,
            flow_velocity_mps=0.0,
            quality_status="valid",
        ),
    ]

    features = FeatureBuilder(lookback_minutes=30, short_window_minutes=5).build(
        yolo, rows, yolo_history
    )

    assert features.water_level_latest == 30
    assert features.flow_velocity_latest == pytest.approx(0.2)
    assert features.sensor_count_30m == 3
    assert features.sensor_valid_ratio_30m == pytest.approx(0.75)
    assert features.water_level_delta_30m == 20
    assert features.water_level_delta_5m == 10
    assert features.water_level_slope_30m == pytest.approx(20 / 29)
    assert features.sensor_age_seconds == 60
    assert features.obstruction_mean_30m == pytest.approx(0.3)
    assert features.obstruction_delta_30m == pytest.approx(0.2)
