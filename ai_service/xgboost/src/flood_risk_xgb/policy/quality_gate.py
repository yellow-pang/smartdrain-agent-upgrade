"""Input quality rules that decide whether model inference is valid."""

from __future__ import annotations

from dataclasses import dataclass, field

from flood_risk_xgb.domain import DataQuality, StateCode, YoloResult
from flood_risk_xgb.features.schema import FeatureVector


@dataclass(frozen=True)
class QualityGateResult:
    can_predict: bool
    reason: str
    data_quality: DataQuality
    state_code: StateCode | None = None
    warnings: list[str] = field(default_factory=list)


class QualityGate:
    def __init__(
        self,
        max_sensor_age_seconds: int,
        min_sensor_count_30m: int,
        min_yolo_confidence: float,
        allow_sensor_danger_override: bool = True,
    ) -> None:
        self.max_sensor_age_seconds = max_sensor_age_seconds
        self.min_sensor_count_30m = min_sensor_count_30m
        self.min_yolo_confidence = min_yolo_confidence
        self.allow_sensor_danger_override = allow_sensor_danger_override

    @staticmethod
    def _sensor_indicates_clear_danger(features: FeatureVector) -> bool:
        return (
            features.water_level_latest >= 80.0
            and (
                features.flow_velocity_latest <= 0.15
                or features.water_level_delta_5m >= 8.0
                or features.water_level_delta_30m >= 20.0
            )
        ) or (
            features.water_level_latest >= 70.0
            and features.flow_velocity_latest <= 0.12
            and features.water_level_delta_30m >= 10.0
        )

    def evaluate(self, yolo_result: YoloResult, features: FeatureVector) -> QualityGateResult:
        warnings: list[str] = []

        if features.sensor_age_seconds > self.max_sensor_age_seconds:
            return QualityGateResult(
                can_predict=False,
                reason=(
                    "Latest valid sensor record is stale: "
                    f"{features.sensor_age_seconds:.0f}s > {self.max_sensor_age_seconds}s"
                ),
                data_quality=DataQuality.STALE,
                state_code=StateCode.STALE_SENSOR_DATA,
            )

        severe_sensor_signal = self._sensor_indicates_clear_danger(features)

        if features.sensor_count_30m < self.min_sensor_count_30m:
            if severe_sensor_signal and self.allow_sensor_danger_override:
                warnings.append(
                    "Sensor history count is below the preferred minimum, but current sensor values "
                    "indicate clear danger."
                )
            else:
                return QualityGateResult(
                    can_predict=False,
                    reason=(
                        "Insufficient valid sensor history: "
                        f"{features.sensor_count_30m:.0f} < {self.min_sensor_count_30m}"
                    ),
                    data_quality=DataQuality.INSUFFICIENT,
                    state_code=StateCode.INSUFFICIENT_SENSOR_HISTORY,
                )

        if features.sensor_valid_ratio_30m < 0.40:
            warnings.append(
                "Less than 40% of sensor records in the lookback window are valid."
            )

        low_yolo_quality = (
            yolo_result.confidence_score < self.min_yolo_confidence
            or yolo_result.yolo_status in {"unknown", "failed", "error", "판단불가"}
        )
        if low_yolo_quality:
            if severe_sensor_signal and self.allow_sensor_danger_override:
                warnings.append(
                    "YOLO confidence/status is low, but severe sensor evidence allows sensor-led "
                    "risk inference."
                )
            else:
                return QualityGateResult(
                    can_predict=False,
                    reason=(
                        "YOLO result is not reliable enough and sensor evidence is not decisive "
                        f"(confidence={yolo_result.confidence_score:.3f}, "
                        f"status={yolo_result.yolo_status})."
                    ),
                    data_quality=DataQuality.SUSPECT,
                    state_code=StateCode.LOW_CONFIDENCE_VISION,
                )

        data_quality = DataQuality.VALID
        if warnings:
            data_quality = DataQuality.SUSPECT

        return QualityGateResult(
            can_predict=True,
            reason="Input quality checks passed.",
            data_quality=data_quality,
            warnings=warnings,
        )
