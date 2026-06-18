"""Domain models shared by repositories, feature engineering, and inference."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


class RiskLevel(StrEnum):
    GOOD = "good"
    CAUTION = "caution"
    DANGER = "danger"
    UNKNOWN = "unknown"


class FinalDecision(StrEnum):
    NORMAL = "normal"
    MONITORING = "monitoring"
    FIELD_CHECK = "field_check"
    DISPATCH_REQUIRED = "dispatch_required"
    REVIEW_REQUIRED = "review_required"


class AnalysisStatus(StrEnum):
    COMPLETED = "completed"
    DEGRADED = "degraded"
    SKIPPED = "skipped"
    FAILED = "failed"


class DataQuality(StrEnum):
    VALID = "valid"
    SUSPECT = "suspect"
    STALE = "stale"
    INSUFFICIENT = "insufficient"
    INVALID = "invalid"


class StateCode(StrEnum):
    NORMAL_DRAINAGE = "NORMAL_DRAINAGE"
    SURFACE_OBSTRUCTION_LIKELY = "SURFACE_OBSTRUCTION_LIKELY"
    DRY_SURFACE_OBSTRUCTION = "DRY_SURFACE_OBSTRUCTION"
    DRAINING_WITH_SURFACE_OBSTRUCTION = "DRAINING_WITH_SURFACE_OBSTRUCTION"
    COMBINED_OBSTRUCTION = "COMBINED_OBSTRUCTION"
    SEVERE_OBSTRUCTION = "SEVERE_OBSTRUCTION"
    INTERNAL_OR_DOWNSTREAM_OBSTRUCTION_SUSPECTED = "INTERNAL_OR_DOWNSTREAM_OBSTRUCTION_SUSPECTED"
    PROGRESSIVE_OBSTRUCTION = "PROGRESSIVE_OBSTRUCTION"
    INTERMITTENT_OBSTRUCTION = "INTERMITTENT_OBSTRUCTION"
    HYDRAULIC_OVERLOAD = "HYDRAULIC_OVERLOAD"
    HIGH_INFLOW_WITH_SURFACE_OBSTRUCTION = "HIGH_INFLOW_WITH_SURFACE_OBSTRUCTION"
    NEAR_CAPACITY_STABLE = "NEAR_CAPACITY_STABLE"
    RECOVERING = "RECOVERING"
    VISION_SENSOR_CONFLICT = "VISION_SENSOR_CONFLICT"
    SENSOR_DETECTED_HIDDEN_RISK = "SENSOR_DETECTED_HIDDEN_RISK"
    WATER_LEVEL_SPIKE = "WATER_LEVEL_SPIKE"
    FLOW_SENSOR_STUCK = "FLOW_SENSOR_STUCK"
    SENSOR_OSCILLATION = "SENSOR_OSCILLATION"
    STALE_SENSOR_DATA = "STALE_SENSOR_DATA"
    NO_VALID_SENSOR_DATA = "NO_VALID_SENSOR_DATA"
    INSUFFICIENT_SENSOR_HISTORY = "INSUFFICIENT_SENSOR_HISTORY"
    LOW_CONFIDENCE_VISION = "LOW_CONFIDENCE_VISION"
    UNKNOWN_STATE = "UNKNOWN_STATE"


class SensorQuality(StrEnum):
    VALID = "valid"
    MISSING = "missing"
    SUSPECT = "suspect"
    INVALID = "invalid"


class YoloResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    yolo_result_id: int = Field(ge=1)
    drain_id: int = Field(ge=1)
    captured_at: datetime
    image_uri: str = Field(
        validation_alias=AliasChoices("image_uri", "image_url"),
        serialization_alias="image_uri",
    )
    obstruction_ratio: float = Field(ge=0.0, le=1.0)
    confidence_score: float = Field(ge=0.0, le=1.0)
    yolo_status: str
    # false rows are retained only as recent YOLO history. run_pending_analysis skips them.
    analysis_target: bool = True

    @field_validator("yolo_status")
    @classmethod
    def normalize_status(cls, value: str) -> str:
        return value.strip().lower()


class SensorRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    measured_at: datetime
    drain_id: int = Field(ge=1)
    water_level_cm: float = Field(ge=0.0)
    flow_velocity_mps: float = Field(ge=0.0)
    quality_status: SensorQuality = SensorQuality.VALID


class XgboostResult(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    xgboost_id: int | None = Field(default=None, ge=1)
    drain_id: int = Field(ge=1)
    sensor_measured_at: datetime | None
    yolo_result_id: int = Field(ge=1)
    evaluated_at: datetime
    risk_score: float | None = Field(default=None, ge=0.0, le=1.0)
    risk_level: RiskLevel
    final_decision: FinalDecision
    analysis_status: AnalysisStatus = AnalysisStatus.COMPLETED
    data_quality: DataQuality = DataQuality.VALID
    state_code: StateCode = StateCode.UNKNOWN_STATE
    reason_codes: list[str] = Field(default_factory=list)


class AnalysisTrace(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    xgboost_id: int | None = Field(default=None, ge=1)
    yolo_result_id: int = Field(ge=1)
    drain_id: int = Field(ge=1)
    sensor_window_start: datetime | None
    sensor_window_end: datetime
    model_version: str
    feature_values: dict[str, float] | None
    class_probabilities: dict[str, float] | None
    decision_reason: str
    warnings: list[str] = Field(default_factory=list)
    analysis_status: AnalysisStatus = AnalysisStatus.COMPLETED
    data_quality: DataQuality = DataQuality.VALID
    state_code: StateCode = StateCode.UNKNOWN_STATE
    reason_codes: list[str] = Field(default_factory=list)
    source_refs: dict[str, Any] = Field(default_factory=dict)
