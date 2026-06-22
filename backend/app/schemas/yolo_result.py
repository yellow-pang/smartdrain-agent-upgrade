"""
YOLO 분석 결과 API 요청과 응답 구조를 정의하는 Pydantic 스키마 파일입니다.

주요 역할:
- YOLO 분석 결과 생성 요청 모델 정의
- 이미지 URL, 막힘 비율, 신뢰도, 상태 응답 모델 정의
- ORM 객체 기반 응답 변환 설정
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class YoloResultBase(BaseModel):
    drain_id: int = Field(alias="drainId")
    image_url: str | None = Field(default=None, alias="imageUrl")
    obstruction_ratio: float | None = Field(default=None, alias="obstructionRatio")
    confidence_score: float | None = Field(default=None, alias="confidenceScore")
    yolo_status: str = Field(default="unknown", alias="yoloStatus")  # clear, partially_blocked, blocked, unknown
    captured_at: datetime | None = Field(default=None, alias="capturedAt")

    model_config = ConfigDict(populate_by_name=True)


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
