import math
import re
from datetime import datetime

from ai_service.image_source.service import resolve_image_source_by_drain_id

REQUIRED_TOP_LEVEL_KEYS = ("request_id", "drain_id", "sensor_data")
REQUIRED_SENSOR_KEYS = (
    "measured_at",
    "water_level_cm",
    "flow_velocity_mps",
    "quality_status",
)


def validate_analysis_request(payload: dict) -> None:
    if not isinstance(payload, dict):
        raise ValueError("analysis request payload must be a dict.")

    missing_keys = [key for key in REQUIRED_TOP_LEVEL_KEYS if key not in payload]
    if missing_keys:
        raise ValueError(f"Missing required analysis request keys: {missing_keys}")

    sensor_data = payload["sensor_data"]
    if not isinstance(sensor_data, dict):
        raise ValueError("sensor_data must be a dict.")

    missing_sensor_keys = [
        key for key in REQUIRED_SENSOR_KEYS if key not in sensor_data
    ]
    if missing_sensor_keys:
        raise ValueError(f"Missing required sensor_data keys: {missing_sensor_keys}")

    _validate_non_empty_string(payload["request_id"], "request_id")
    _validate_drain_identifier(payload["drain_id"], "drain_id")
    _validate_iso_datetime_string(sensor_data["measured_at"], "sensor_data.measured_at")
    _validate_finite_number(sensor_data["water_level_cm"], "sensor_data.water_level_cm")
    _validate_finite_number(
        sensor_data["flow_velocity_mps"],
        "sensor_data.flow_velocity_mps",
    )

    if sensor_data["quality_status"] != "valid":
        raise ValueError("sensor_data.quality_status must be 'valid'.")


def validate_analysis_image_source(payload: dict) -> None:
    """Validate that the request can resolve to a configured image source."""
    # 등록되지 않은 drain_id는 CCTV/스토리지 소스 설정 이상으로 본다.
    # background task까지 넘기지 않고 HTTP 요청 단계에서 거절하기 위한 사전 검증이다.
    resolve_image_source_by_drain_id(payload["drain_id"])


def _validate_non_empty_string(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")


def _validate_drain_identifier(value: object, field_name: str) -> None:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer or DR-### code.")
    if isinstance(value, int):
        return
    if isinstance(value, str) and value.strip():
        stripped = value.strip()
        if stripped.isdigit() or re.fullmatch(
            r"DR-\d+",
            stripped,
            flags=re.IGNORECASE,
        ):
            return
    raise ValueError(f"{field_name} must be an integer or DR-### code.")


def _validate_iso_datetime_string(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be an ISO datetime string.")

    stripped = value.strip()
    if "T" not in stripped:
        raise ValueError(f"{field_name} must be an ISO datetime string.")

    normalized = stripped.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string.") from exc


def _validate_finite_number(value: object, field_name: str) -> None:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a finite number.")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a finite number.") from exc

    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be a finite number.")
