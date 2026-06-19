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

    if sensor_data["quality_status"] != "valid":
        raise ValueError("sensor_data.quality_status must be 'valid'.")
