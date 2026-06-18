"""
백엔드 환경 설정 값을 관리하는 설정 파일입니다.

주요 역할:
- 프로젝트 이름, 데이터베이스 URL, CORS 허용 출처 정의
- 환경 변수 기반 설정 로드
- CORS 출처 문자열 파싱
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Flood Monitoring Backend"
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/flood_db"
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    model_config = SettingsConfigDict(env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
