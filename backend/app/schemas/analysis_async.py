"""
AI 서버 비동기 분석 시작 API의 요청과 응답 구조를 정의하는 스키마 파일입니다.

주요 역할:
- 비동기 분석 시작 요청 body 정의
- AI 서버 job 시작 응답 구조 정의
- 프론트 응답용 분석 요청 DTO 정의
"""

from pydantic import BaseModel, ConfigDict, Field


class AnalysisAsyncRunRequest(BaseModel):
    drain_id: str = Field(alias="drainId")

    model_config = ConfigDict(populate_by_name=True)


class AiAnalysisRunResponse(BaseModel):
    accepted: bool
    request_id: str
    job_id: str | None = None
    status: str


class AnalysisAsyncRunDto(BaseModel):
    request_id: str = Field(alias="requestId")
    job_id: str | None = Field(default=None, alias="jobId")
    drain_id: str = Field(alias="drainId")
    status: str
    sensor_summary: dict[str, object] = Field(alias="sensorSummary")

    model_config = ConfigDict(populate_by_name=True)
