"""
AI 서버 callback 요청 구조를 정의하는 Pydantic 스키마 파일입니다.

주요 역할:
- YOLO 중간 결과 callback 요청 모델 정의
- XGBoost 최종 결과 callback 요청 모델 정의
- request_id와 job_id 기반 분석 요청 식별값 정의
"""

from datetime import datetime

from pydantic import BaseModel, Field


class AiCallbackBase(BaseModel):
    request_id: str
    job_id: str | None = None


class AiYoloResultPayload(BaseModel):
    obstruction_ratio: float
    confidence_score: float
    yolo_status: str


class AiYoloCallbackRequest(AiCallbackBase):
    yolo_result: AiYoloResultPayload


class AiXgboostResultPayload(BaseModel):
    risk_score: float
    risk_level: str
    final_decision: str
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


class AiXgboostCallbackRequest(AiCallbackBase):
    xgboost_result: AiXgboostResultPayload
