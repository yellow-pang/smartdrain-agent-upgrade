WATER_LEVEL_NORMALIZATION_CM = 100.0
FLOW_VELOCITY_NORMALIZATION_MPS = 1.0


def build_xgboost_input_batch(sensor_data: dict, yolo_result: dict) -> dict:
    return {
        "obstruction_ratio": [yolo_result["obstruction_ratio"]],
        "confidence_score": [yolo_result["confidence_score"]],
        "water_level": [
            _normalize_to_unit_range(
                sensor_data["water_level_cm"],
                WATER_LEVEL_NORMALIZATION_CM,
            )
        ],
        "flow_velocity": [
            _normalize_to_unit_range(
                sensor_data["flow_velocity_mps"],
                FLOW_VELOCITY_NORMALIZATION_MPS,
            )
        ],
    }


def _normalize_to_unit_range(value: float, denominator: float) -> float:
    normalized = float(value) / denominator
    return min(max(normalized, 0.0), 1.0)

