"""
하수구 API 요청과 응답 구조를 정의하는 Pydantic 스키마 파일입니다.

주요 역할:
- 하수구 기본 입력 필드 정의
- 하수구 생성 요청 모델 정의
- 하수구 조회 응답 모델 정의
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DrainBase(BaseModel):
    drain_code: str = Field(alias="drainCode")
    name: str
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    status: str = "unknown"  # good, caution, danger, unknown

    model_config = ConfigDict(populate_by_name=True)


class DrainCreate(DrainBase):
    pass


class DrainRead(DrainBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DrainResponse(DrainRead):
    pass
