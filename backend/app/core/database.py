"""
데이터베이스 연결과 세션 생성을 담당하는 파일입니다.

주요 역할:
- SQLAlchemy Base 클래스 정의
- 데이터베이스 엔진과 세션 팩토리 생성
- 요청 단위 DB 세션 의존성 제공
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 10})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
