from pydantic import BaseModel, ConfigDict


class DashboardSummary(BaseModel):
    total_drains: int
    good_count: int
    caution_count: int
    danger_count: int
    unknown_count: int


class DashboardDrainStatus(BaseModel):
    drain_id: int
    drain_code: str
    name: str
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    status: str  # good, caution, danger, unknown
    latest_risk_score: float | None = None
    latest_risk_level: str | None = None

    model_config = ConfigDict(from_attributes=True)
