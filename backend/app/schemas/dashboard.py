"""
대시보드 API 응답 구조를 정의하는 Pydantic 스키마 파일입니다.

주요 역할:
- 전체 하수구 상태 요약 응답 모델 정의
- 하수구별 대시보드 상태 응답 모델 정의
"""

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
