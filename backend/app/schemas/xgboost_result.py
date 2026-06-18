"""
XGBoost 위험도 평가 API 요청과 응답 구조를 정의하는 Pydantic 스키마 파일입니다.

주요 역할:
- 위험도 평가 생성 요청 모델 정의
- 위험 점수, 등급, 최종 판단을 포함한 응답 모델 정의
- ORM 객체 기반 응답 변환 설정
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class XgboostResultCreate(BaseModel):
    drain_id: int
    sensor_data_id: int | None = None
    yolo_result_id: int | None = None


class XgboostResultRead(BaseModel):
    id: int
    drain_id: int
    sensor_data_id: int | None
    yolo_result_id: int | None
    risk_score: float
    risk_level: str  # good, caution, danger, unknown
    final_decision: str
    evaluated_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class XgboostResultResponse(XgboostResultRead):
    pass
