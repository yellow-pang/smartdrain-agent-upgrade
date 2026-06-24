import math

from .constants import YOLO_RESULT_FIELDS, YOLO_STATUSES

YOLO_UNKNOWN_SENTINEL = -1.0


def validate_yolo_result_contract(result: dict) -> None:
    if not isinstance(result, dict):
        raise ValueError("YOLO result must be a dict.")

    missing_fields = [field for field in YOLO_RESULT_FIELDS if field not in result]
    if missing_fields:
        raise ValueError(f"Missing YOLO result fields: {missing_fields}")

    if result["yolo_status"] not in YOLO_STATUSES:
        raise ValueError(f"Unsupported yolo_status: {result['yolo_status']}")

    obstruction_ratio = _require_finite_number(
        result["obstruction_ratio"],
        "obstruction_ratio",
    )
    confidence_score = _require_finite_number(
        result["confidence_score"],
        "confidence_score",
    )

    if result["yolo_status"] == "unknown":
        _validate_unknown_sentinel(obstruction_ratio, "obstruction_ratio")
        _validate_unknown_sentinel(confidence_score, "confidence_score")
        return

    _validate_unit_range(obstruction_ratio, "obstruction_ratio")
    _validate_unit_range(confidence_score, "confidence_score")


def _require_finite_number(value: object, field_name: str) -> float:
    if isinstance(value, bool) or isinstance(value, str):
        raise ValueError(f"{field_name} must be a finite number.")

    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a finite number.") from exc

    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be a finite number.")
    return number


def _validate_unknown_sentinel(value: float, field_name: str) -> None:
    if value != YOLO_UNKNOWN_SENTINEL:
        raise ValueError(f"{field_name} must be -1.0 when yolo_status is unknown.")


def _validate_unit_range(value: float, field_name: str) -> None:
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0.")
