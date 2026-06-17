from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DrainBase(BaseModel):
    drain_code: str
    name: str
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    status: str = "unknown"  # good, caution, danger, unknown


class DrainCreate(DrainBase):
    pass


class DrainRead(DrainBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DrainResponse(DrainRead):
    pass
