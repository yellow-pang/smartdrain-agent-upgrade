"""
이미지 분석과 위험도 평가 API를 처리하는 라우터 파일입니다.

주요 역할:
- YOLO 분석 결과 생성 API 정의
- XGBoost 위험도 평가 결과 생성 및 WebSocket 알림 전송
- 하수구별 분석 결과와 위험도 이력 조회 API 정의
"""

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.api_response import (
    api_list_response,
    api_response,
    drain_status_event_payload,
    risk_history_dto,
    xgboost_result_dto,
    yolo_result_dto,
)
from app.schemas.xgboost_result import XgboostResultCreate
from app.schemas.yolo_result import YoloResultCreate
from app.schemas.analysis_async import AnalysisAsyncRunRequest
from app.services import xgboost_service, yolo_service
from app.services import analysis_async_service
from app.services.drain_service import get_drain_by_identifier
from app.websocket.manager import manager

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analysis/async-run")
async def run_async_analysis(payload: AnalysisAsyncRunRequest, db: Session = Depends(get_db)):
    result = await analysis_async_service.start_async_analysis(db, payload)
    return api_response(result, message="Analysis request accepted")


@router.post("/analysis/yolo", status_code=201)
def create_yolo_result(payload: YoloResultCreate, db: Session = Depends(get_db)):
    result = yolo_service.create_yolo_result(db, payload)
    return api_response(yolo_result_dto(result), message="YOLO analysis result created")


@router.post("/analysis/xgboost", status_code=201)
async def create_xgboost_result(payload: XgboostResultCreate, db: Session = Depends(get_db)):
    result = xgboost_service.evaluate_risk(db, payload)
    await manager.broadcast(json.dumps(drain_status_event_payload(db, result.drain, result)))
    return api_response(xgboost_result_dto(result), message="Risk analysis result created")


@router.get("/drains/{drain_id}/yolo-results")
def list_yolo_results(drain_id: str, db: Session = Depends(get_db)):
    drain = get_drain_by_identifier(db, drain_id)
    results = yolo_service.get_yolo_results_by_drain(db, drain.id)
    return api_list_response([yolo_result_dto(result) for result in results])


@router.get("/drains/{drain_id}/analysis/yolo")
def yolo_analysis_history(
    drain_id: str,
    limit: int = Query(default=10, ge=1),
    db: Session = Depends(get_db),
):
    drain = get_drain_by_identifier(db, drain_id)
    results = yolo_service.get_yolo_results_by_drain(db, drain.id, limit=limit)
    return api_list_response([yolo_result_dto(result) for result in results])


@router.get("/drains/{drain_id}/analysis/xgboost")
def xgboost_analysis_history(
    drain_id: str,
    limit: int = Query(default=10, ge=1),
    db: Session = Depends(get_db),
):
    drain = get_drain_by_identifier(db, drain_id)
    results = xgboost_service.get_risk_history(db, drain.id, limit=limit)
    return api_list_response([xgboost_result_dto(result) for result in results])


@router.get("/drains/{drain_id}/analysis/history")
def analysis_history(
    drain_id: str,
    limit: int = Query(default=10, ge=1),
    db: Session = Depends(get_db),
):
    drain = get_drain_by_identifier(db, drain_id)
    yolo_results = yolo_service.get_yolo_results_by_drain(db, drain.id, limit=limit)
    xgboost_results = xgboost_service.get_risk_history(db, drain.id, limit=limit)
    return api_response(
        {
            "drainId": drain.drain_code,
            "yoloResults": [yolo_result_dto(result) for result in yolo_results],
            "xgboostResults": [xgboost_result_dto(result) for result in xgboost_results],
        }
    )


@router.get("/drains/{drain_id}/risk-history")
def risk_history(
    drain_id: str,
    limit: int | None = Query(default=None, ge=1),
    days: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
):
    # TODO: MVP 이후 days query를 기간 필터링에 반영합니다.
    drain = get_drain_by_identifier(db, drain_id)
    results = xgboost_service.get_risk_history(db, drain.id, limit=limit)
    return api_list_response([risk_history_dto(result) for result in results])


@router.get("/drains/{drain_id}/risk/latest")
def latest_risk(drain_id: str, db: Session = Depends(get_db)):
    drain = get_drain_by_identifier(db, drain_id)
    result = xgboost_service.get_latest_risk(db, drain.id)
    return api_response(xgboost_result_dto(result))
