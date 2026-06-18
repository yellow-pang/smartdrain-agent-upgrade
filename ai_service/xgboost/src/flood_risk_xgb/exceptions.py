"""Domain-specific exceptions."""


class FloodRiskError(Exception):
    """Base exception for the XGBoost service."""


class RecordNotFoundError(FloodRiskError):
    """Requested mock or DB record does not exist."""


class DuplicateAnalysisError(FloodRiskError):
    """The same YOLO result has already been analyzed."""


class InsufficientSensorDataError(FloodRiskError):
    """No usable sensor data is available for feature construction."""


class ModelContractError(FloodRiskError):
    """Model metadata and runtime features are inconsistent."""
