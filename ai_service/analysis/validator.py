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

    if sensor_data["quality_status"] != "valid":
        raise ValueError("sensor_data.quality_status must be 'valid'.")


def validate_analysis_image_source(payload: dict) -> None:
    """Validate that the request can resolve to a configured image source."""
    # 등록되지 않은 drain_id는 CCTV/스토리지 소스 설정 이상으로 본다.
    # background task까지 넘기지 않고 HTTP 요청 단계에서 거절하기 위한 사전 검증이다.
    resolve_image_source_by_drain_id(payload["drain_id"])
