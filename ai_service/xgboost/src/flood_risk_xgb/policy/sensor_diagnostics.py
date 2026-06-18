"""Raw sensor quality checks that run before XGBoost inference."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import fmean, pstdev

from flood_risk_xgb.domain import DataQuality, SensorQuality, SensorRecord, StateCode


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class SensorDiagnosticsResult:
    data_quality: DataQuality
    state_code: StateCode | None = None
    reason_codes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    can_attempt_prediction: bool = True


class SensorDiagnostics:
    """Detect obvious sensor errors before a single bad point enters the model."""

    def __init__(self, max_sensor_age_seconds: int) -> None:
        self.max_sensor_age_seconds = max_sensor_age_seconds

    def evaluate(
        self,
        sensor_records: list[SensorRecord],
        reference_time: datetime,
    ) -> SensorDiagnosticsResult:
        reference_utc = _as_utc(reference_time)
        valid = [
            row
            for row in sensor_records
            if row.quality_status == SensorQuality.VALID
            and _as_utc(row.measured_at) <= reference_utc
        ]
        valid.sort(key=lambda row: _as_utc(row.measured_at))

        if not valid:
            return SensorDiagnosticsResult(
                data_quality=DataQuality.INVALID,
                state_code=StateCode.NO_VALID_SENSOR_DATA,
                reason_codes=["NO_VALID_SENSOR_DATA"],
                warnings=["No valid sensor record exists in the lookback window."],
                can_attempt_prediction=False,
            )

        latest = valid[-1]
        sensor_age = (reference_utc - _as_utc(latest.measured_at)).total_seconds()
        if sensor_age > self.max_sensor_age_seconds:
            return SensorDiagnosticsResult(
                data_quality=DataQuality.STALE,
                state_code=StateCode.STALE_SENSOR_DATA,
                reason_codes=["STALE_SENSOR_DATA"],
                warnings=[f"Latest sensor record is {sensor_age:.0f}s old."],
                can_attempt_prediction=False,
            )

        warnings: list[str] = []
        reason_codes: list[str] = []
        state_code: StateCode | None = None

        if len(valid) >= 6:
            previous = valid[:-1]
            previous_water = [row.water_level_cm for row in previous]
            previous_flow = [row.flow_velocity_mps for row in previous]
            water_mean = float(fmean(previous_water))
            water_std = float(pstdev(previous_water)) if len(previous_water) >= 2 else 0.0
            latest_water = latest.water_level_cm
            if latest_water - water_mean >= max(35.0, 6.0 * max(water_std, 1.0)):
                warnings.append("Latest water level looks like an isolated spike.")
                reason_codes.append("WATER_LEVEL_SPIKE")
                state_code = StateCode.WATER_LEVEL_SPIKE

            recent = valid[-10:]
            recent_flow = [row.flow_velocity_mps for row in recent]
            recent_water = [row.water_level_cm for row in recent]
            flow_std = float(pstdev(recent_flow)) if len(recent_flow) >= 2 else 0.0
            water_span = max(recent_water) - min(recent_water)
            if flow_std <= 0.002 and water_span >= 3.0:
                warnings.append("Flow velocity appears stuck while water level changes.")
                reason_codes.append("FLOW_SENSOR_STUCK")
                state_code = state_code or StateCode.FLOW_SENSOR_STUCK

            if len(recent_water) >= 6:
                sign_changes = 0
                deltas = [recent_water[i + 1] - recent_water[i] for i in range(len(recent_water) - 1)]
                for left, right in zip(deltas, deltas[1:]):
                    if left * right < 0 and abs(left) >= 10.0 and abs(right) >= 10.0:
                        sign_changes += 1
                if sign_changes >= 3:
                    warnings.append("Water level oscillates unrealistically in recent records.")
                    reason_codes.append("SENSOR_OSCILLATION")
                    state_code = state_code or StateCode.SENSOR_OSCILLATION

        if reason_codes:
            return SensorDiagnosticsResult(
                data_quality=DataQuality.SUSPECT,
                state_code=state_code,
                reason_codes=reason_codes,
                warnings=warnings,
                can_attempt_prediction=True,
            )

        return SensorDiagnosticsResult(data_quality=DataQuality.VALID)
