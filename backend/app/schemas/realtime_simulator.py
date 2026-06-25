"""
실시간 대시보드 자동 시뮬레이터 API 스키마를 정의합니다.
"""

from pydantic import BaseModel, ConfigDict, Field


class RealtimeSimulatorStartRequest(BaseModel):
    interval_seconds: int | None = Field(default=None, alias="intervalSeconds", ge=5, le=300)

    model_config = ConfigDict(populate_by_name=True)


class RealtimeSimulatorStatusDto(BaseModel):
    running: bool
    interval_seconds: int = Field(alias="intervalSeconds")
    started_at: str | None = Field(default=None, alias="startedAt")
    last_tick_at: str | None = Field(default=None, alias="lastTickAt")
    last_run_drain_count: int = Field(alias="lastRunDrainCount")
    total_run_count: int = Field(alias="totalRunCount")
    last_error: str | None = Field(default=None, alias="lastError")
    trigger_type: str = Field(alias="triggerType")

    model_config = ConfigDict(populate_by_name=True)
