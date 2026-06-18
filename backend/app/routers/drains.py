"""
하수구 정보 API를 처리하는 라우터 파일입니다.

주요 역할:
- 하수구 목록 조회 API 정의
- 단일 하수구 조회 API 정의
- 하수구 등록 API 정의
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.api_response import (
    analysis_latest_dto,
    api_list_response,
    api_response,
    drain_detail_dto,
    drain_list_item_dto,
)
from app.schemas.drain import DrainCreate
from app.services import drain_service

router = APIRouter(prefix="/api/drains", tags=["drains"])


@router.get("")
def list_drains(db: Session = Depends(get_db)):
    drains = drain_service.get_drains(db)
    return api_list_response([drain_list_item_dto(db, drain) for drain in drains])


@router.get("/{drain_id}/analysis/latest")
def latest_analysis(drain_id: str, db: Session = Depends(get_db)):
    drain = drain_service.get_drain_by_identifier(db, drain_id)
    return api_response(analysis_latest_dto(db, drain))


@router.get("/{drain_id}")
def get_drain(drain_id: str, db: Session = Depends(get_db)):
    drain = drain_service.get_drain_by_identifier(db, drain_id)
    return api_response(drain_detail_dto(db, drain))


@router.post("", status_code=201)
def create_drain(payload: DrainCreate, db: Session = Depends(get_db)):
    drain = drain_service.create_drain(db, payload)
    return api_response(drain_detail_dto(db, drain), message="Drain created")
