"""Build temporal XGBoost features without future-data leakage."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from statistics import fmean, pstdev

from flood_risk_xgb.domain import SensorQuality, SensorRecord, YoloResult
from flood_risk_xgb.exceptions import InsufficientSensorDataError
from flood_risk_xgb.features.schema import FeatureVector


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _mean(values: list[float]) -> float:
    return float(fmean(values))


def _delta(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return float(values[-1] - values[0])


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return float(pstdev(values))


def _slope(values: list[float], rows: list[SensorRecord]) -> float:
    if len(values) < 2:
        return 0.0
    minutes = (_as_utc(rows[-1].measured_at) - _as_utc(rows[0].measured_at)).total_seconds() / 60.0
    if minutes <= 0:
        return 0.0
    return float((values[-1] - values[0]) / minutes)


class FeatureBuilder:
    def __init__(self, lookback_minutes: int = 30, short_window_minutes: int = 5) -> None:
        if lookback_minutes <= 0:
            raise ValueError("lookback_minutes must be positive")
        if short_window_minutes <= 0 or short_window_minutes > lookback_minutes:
            raise ValueError("short_window_minutes must be within the lookback window")
        self.lookback_minutes = lookback_minutes
        self.short_window_minutes = short_window_minutes

    def build(
        self,
        yolo_result: YoloResult,
        sensor_records: list[SensorRecord],
        yolo_history: list[YoloResult] | None = None,
    ) -> FeatureVector:
        reference_time = _as_utc(yolo_result.captured_at)
        lookback_start = reference_time - timedelta(minutes=self.lookback_minutes)
        short_start = reference_time - timedelta(minutes=self.short_window_minutes)

        raw_in_window = [
            row
            for row in sensor_records
            if row.drain_id == yolo_result.drain_id
            and lookback_start <= _as_utc(row.measured_at) <= reference_time
        ]
        raw_in_window.sort(key=lambda row: _as_utc(row.measured_at))

        usable = [row for row in raw_in_window if row.quality_status == SensorQuality.VALID]
        usable.sort(key=lambda row: _as_utc(row.measured_at))

        if not usable:
            raise InsufficientSensorDataError(
                "No valid sensor records exist in the configured lookback window"
            )

        short_rows = [row for row in usable if _as_utc(row.measured_at) >= short_start]
        if not short_rows:
            short_rows = [usable[-1]]

        history_source = list(yolo_history or []) + [yolo_result]
        yolo_rows = [
            row
            for row in history_source
            if row.drain_id == yolo_result.drain_id
            and lookback_start <= _as_utc(row.captured_at) <= reference_time
        ]
        yolo_rows.sort(key=lambda row: _as_utc(row.captured_at))
        if not yolo_rows:
            yolo_rows = [yolo_result]
        obstruction_values = [row.obstruction_ratio for row in yolo_rows]

        latest = usable[-1]
        water_5m = [row.water_level_cm for row in short_rows]
        flow_5m = [row.flow_velocity_mps for row in short_rows]
        water_30m = [row.water_level_cm for row in usable]
        flow_30m = [row.flow_velocity_mps for row in usable]

        age_seconds = max(
            0.0,
            (reference_time - _as_utc(latest.measured_at)).total_seconds(),
        )
        valid_ratio = len(usable) / max(len(raw_in_window), 1)

        return FeatureVector(
            obstruction_ratio=yolo_result.obstruction_ratio,
            confidence_score=yolo_result.confidence_score,
            obstruction_mean_30m=_mean(obstruction_values),
            obstruction_delta_30m=_delta(obstruction_values),
            obstruction_persistence_count_30m=float(
                sum(1 for value in obstruction_values if value >= 0.65)
            ),
            water_level_latest=latest.water_level_cm,
            flow_velocity_latest=latest.flow_velocity_mps,
            water_level_mean_5m=_mean(water_5m),
            flow_velocity_mean_5m=_mean(flow_5m),
            water_level_delta_5m=_delta(water_5m),
            flow_velocity_delta_5m=_delta(flow_5m),
            water_level_mean_30m=_mean(water_30m),
            flow_velocity_mean_30m=_mean(flow_30m),
            water_level_delta_30m=_delta(water_30m),
            flow_velocity_delta_30m=_delta(flow_30m),
            water_level_slope_30m=_slope(water_30m, usable),
            flow_velocity_slope_30m=_slope(flow_30m, usable),
            water_level_max_30m=max(water_30m),
            flow_velocity_min_30m=min(flow_30m),
            water_level_std_30m=_std(water_30m),
            flow_velocity_std_30m=_std(flow_30m),
            sensor_age_seconds=age_seconds,
            sensor_count_30m=float(len(usable)),
            sensor_valid_ratio_30m=float(valid_ratio),
        )
