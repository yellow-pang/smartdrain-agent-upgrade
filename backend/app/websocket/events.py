"""
WebSocket 이벤트 타입 상수를 정의하는 파일입니다.

주요 역할:
- 하수구 상태 갱신 이벤트 타입 정의
- YOLO 중간 결과 갱신 이벤트 타입 정의
- XGBoost 최종 결과 갱신 이벤트 타입 정의
"""

DRAIN_STATUS_UPDATED = "DRAIN_STATUS_UPDATED"
YOLO_RESULT_UPDATED = "YOLO_RESULT_UPDATED"
XGBOOST_RESULT_UPDATED = "XGBOOST_RESULT_UPDATED"
