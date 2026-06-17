from datetime import datetime

from pydantic import BaseModel, ConfigDict


class YoloResultBase(BaseModel):
    drain_id: int
    image_url: str | None = None
    obstruction_ratio: float | None = None
    confidence_score: float | None = None
    yolo_status: str = "unknown"  # good, caution, danger, unknown
    captured_at: datetime | None = None


class YoloResultCreate(YoloResultBase):
    pass


class YoloResultRead(BaseModel):
    id: int
    drain_id: int
    image_url: str | None
    obstruction_ratio: float
    confidence_score: float
    yolo_status: str
    captured_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class YoloResultResponse(YoloResultRead):
    pass
