WATER_LEVEL_NORMALIZATION_CM = 100.0
FLOW_VELOCITY_NORMALIZATION_MPS = 1.0


def build_xgboost_input_batch(sensor_data: dict, yolo_result: dict) -> dict:
    # XGBoost 학습 시 사용한 feature 이름과 순서를 유지한다.
    # 센서 원본 단위(cm, m/s)는 모델 입력 범위에 맞춰 0.0~1.0으로 정규화한다.
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
