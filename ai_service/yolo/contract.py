from .constants import YOLO_RESULT_FIELDS, YOLO_STATUSES


def validate_yolo_result_contract(result: dict) -> None:
    if not isinstance(result, dict):
        raise ValueError("YOLO result must be a dict.")

    missing_fields = [field for field in YOLO_RESULT_FIELDS if field not in result]
    if missing_fields:
        raise ValueError(f"Missing YOLO result fields: {missing_fields}")

    if result["yolo_status"] not in YOLO_STATUSES:
        raise ValueError(f"Unsupported yolo_status: {result['yolo_status']}")
