"""Fixed-length feature vector used by the XGBoost model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


FEATURE_COLUMNS = [
    "obstruction_ratio",
    "confidence_score",
    "obstruction_mean_30m",
    "obstruction_delta_30m",
    "obstruction_persistence_count_30m",
    "water_level_latest",
    "flow_velocity_latest",
    "water_level_mean_5m",
    "flow_velocity_mean_5m",
    "water_level_delta_5m",
    "flow_velocity_delta_5m",
    "water_level_mean_30m",
    "flow_velocity_mean_30m",
    "water_level_delta_30m",
    "flow_velocity_delta_30m",
    "water_level_slope_30m",
    "flow_velocity_slope_30m",
    "water_level_max_30m",
    "flow_velocity_min_30m",
    "water_level_std_30m",
    "flow_velocity_std_30m",
    "sensor_age_seconds",
    "sensor_count_30m",
    "sensor_valid_ratio_30m",
]


class FeatureVector(BaseModel):
    model_config = ConfigDict(extra="forbid")

    obstruction_ratio: float = Field(ge=0.0, le=1.0)
    confidence_score: float = Field(ge=0.0, le=1.0)
    obstruction_mean_30m: float = Field(ge=0.0, le=1.0)
    obstruction_delta_30m: float
    obstruction_persistence_count_30m: float = Field(ge=0.0)

    water_level_latest: float = Field(ge=0.0)
    flow_velocity_latest: float = Field(ge=0.0)

    water_level_mean_5m: float = Field(ge=0.0)
    flow_velocity_mean_5m: float = Field(ge=0.0)
    water_level_delta_5m: float
    flow_velocity_delta_5m: float

    water_level_mean_30m: float = Field(ge=0.0)
    flow_velocity_mean_30m: float = Field(ge=0.0)
    water_level_delta_30m: float
    flow_velocity_delta_30m: float
    water_level_slope_30m: float
    flow_velocity_slope_30m: float

    water_level_max_30m: float = Field(ge=0.0)
    flow_velocity_min_30m: float = Field(ge=0.0)
    water_level_std_30m: float = Field(ge=0.0)
    flow_velocity_std_30m: float = Field(ge=0.0)

    sensor_age_seconds: float = Field(ge=0.0)
    sensor_count_30m: float = Field(ge=1.0)
    sensor_valid_ratio_30m: float = Field(ge=0.0, le=1.0)

    def as_ordered_dict(self) -> dict[str, float]:
        raw = self.model_dump()
        return {column: float(raw[column]) for column in FEATURE_COLUMNS}
