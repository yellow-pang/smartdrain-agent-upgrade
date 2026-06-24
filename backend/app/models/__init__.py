"""
SQLAlchemy 모델 클래스를 한 곳에서 가져오도록 모으는 파일입니다.

주요 역할:
- 하수구, 센서 데이터, YOLO 결과, XGBoost 결과 모델 import
- 외부에서 사용할 모델 클래스 목록 정의
"""

from app.models.analysis_job import AnalysisJob
from app.models.drain import Drain
from app.models.sensor_data import SensorData
from app.models.xgboost_result import XgboostResult
from app.models.yolo_result import YoloResult

__all__ = ["AnalysisJob", "Drain", "SensorData", "YoloResult", "XgboostResult"]
