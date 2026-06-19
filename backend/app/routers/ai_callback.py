"""
AI 서버 callback API를 처리하는 라우터 파일입니다.

주요 역할:
- YOLO 중간 결과 callback 수신
- XGBoost 최종 결과 callback 수신
- 저장 결과를 공통 API wrapper로 반환
"""

import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.ai_callback import AiXgboostCallbackRequest, AiYoloCallbackRequest
from app.schemas.api_response import api_response
from app.services import analysis_async_service
from app.websocket.manager import manager

router = APIRouter(prefix="/api/ai-callback", tags=["ai-callback"])


@router.post("/yolo-result")
async def save_yolo_result(payload: AiYoloCallbackRequest, db: Session = Depends(get_db)):
    _, event = analysis_async_service.save_yolo_callback(db, payload)
    await manager.broadcast(json.dumps(event))
    return api_response(data=None, message="YOLO result saved")


@router.post("/xgboost-result")
async def save_xgboost_result(payload: AiXgboostCallbackRequest, db: Session = Depends(get_db)):
    _, xgboost_event, drain_status_event = analysis_async_service.save_xgboost_callback(db, payload)
    await manager.broadcast(json.dumps(xgboost_event))
    await manager.broadcast(json.dumps(drain_status_event))
    return api_response(data=None, message="XGBoost result saved")
