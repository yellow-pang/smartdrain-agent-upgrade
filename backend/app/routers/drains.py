from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.drain import DrainCreate, DrainResponse
from app.services import drain_service

router = APIRouter(prefix="/api/drains", tags=["drains"])


@router.get("", response_model=list[DrainResponse])
def list_drains(db: Session = Depends(get_db)):
    return drain_service.get_drains(db)


@router.get("/{drain_id}", response_model=DrainResponse)
def get_drain(drain_id: int, db: Session = Depends(get_db)):
    return drain_service.get_drain(db, drain_id)


@router.post("", response_model=DrainResponse, status_code=201)
def create_drain(payload: DrainCreate, db: Session = Depends(get_db)):
    return drain_service.create_drain(db, payload)
