"""
Pydantic 스키마 클래스를 한 곳에서 가져오도록 모으는 파일입니다.

주요 역할:
- 대시보드, 하수구, 센서 데이터, 분석 결과 스키마 import
- 외부에서 사용할 스키마 클래스 목록 정의
"""

from app.schemas.dashboard import DashboardDrainStatus, DashboardSummary
from app.schemas.drain import DrainCreate, DrainRead, DrainResponse
from app.schemas.sensor_data import SensorDataCreate, SensorDataRead, SensorDataResponse
from app.schemas.xgboost_result import XgboostResultCreate, XgboostResultRead, XgboostResultResponse
from app.schemas.yolo_result import YoloResultCreate, YoloResultRead, YoloResultResponse

__all__ = [
    "DashboardDrainStatus",
    "DashboardSummary",
    "DrainCreate",
    "DrainRead",
    "DrainResponse",
    "SensorDataCreate",
    "SensorDataRead",
    "SensorDataResponse",
    "YoloResultCreate",
    "YoloResultRead",
    "YoloResultResponse",
    "XgboostResultCreate",
    "XgboostResultRead",
    "XgboostResultResponse",
]
