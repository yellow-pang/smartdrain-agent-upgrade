"""
센서 데이터 API 요청과 응답 구조를 정의하는 Pydantic 스키마 파일입니다.

주요 역할:
- 센서 데이터 생성 요청 모델 정의
- 센서 데이터 조회 응답 모델 정의
- ORM 객체 기반 응답 변환 설정
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SensorDataBase(BaseModel):
    drain_id: int = Field(alias="drainId")
    water_level_cm: float = Field(alias="waterLevelCm")
    flow_velocity_mps: float = Field(alias="flowVelocityMps")
    measured_at: datetime | None = Field(default=None, alias="measuredAt")

    model_config = ConfigDict(populate_by_name=True)


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
