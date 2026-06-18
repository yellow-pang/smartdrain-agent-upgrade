"""
하수구 데이터 조회와 생성을 담당하는 서비스 파일입니다.

주요 역할:
- 하수구 목록 조회
- 단일 하수구 조회 및 미존재 시 예외 처리
- 하수구 신규 등록
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.drain import Drain
from app.schemas.drain import DrainCreate


def get_drains(db: Session) -> list[Drain]:
    return db.query(Drain).order_by(Drain.id).all()


def get_drain(db: Session, drain_id: int) -> Drain:
    drain = db.get(Drain, drain_id)
    if not drain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drain not found")
    return drain


def create_drain(db: Session, payload: DrainCreate) -> Drain:
    drain = Drain(**payload.model_dump())
    db.add(drain)
    db.commit()
    db.refresh(drain)
    return drain
