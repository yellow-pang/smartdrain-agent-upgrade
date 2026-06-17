from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SensorDataBase(BaseModel):
    drain_id: int
    water_level_cm: float
    flow_velocity_mps: float
    measured_at: datetime | None = None


class SensorDataCreate(SensorDataBase):
    pass


class SensorDataRead(BaseModel):
    id: int
    drain_id: int
    water_level_cm: float
    flow_velocity_mps: float
    measured_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SensorDataResponse(SensorDataRead):
    pass
