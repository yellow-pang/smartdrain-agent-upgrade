from datetime import datetime

from pydantic import BaseModel, ConfigDict


class XgboostResultCreate(BaseModel):
    drain_id: int
    sensor_data_id: int | None = None
    yolo_result_id: int | None = None


class XgboostResultRead(BaseModel):
    id: int
    drain_id: int
    sensor_data_id: int | None
    yolo_result_id: int | None
    risk_score: float
    risk_level: str  # good, caution, danger, unknown
    final_decision: str
    evaluated_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class XgboostResultResponse(XgboostResultRead):
    pass
