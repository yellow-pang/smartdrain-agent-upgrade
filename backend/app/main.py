"""
FastAPI 애플리케이션을 생성하고 라우터를 등록하는 진입점 파일입니다.

주요 역할:
- FastAPI 앱 인스턴스 생성
- CORS 미들웨어 설정
- 헬스 체크 API와 주요 라우터 등록
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.routers import analysis, dashboard, drains, sensor_data, websocket
from app.schemas.api_response import api_response


app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check() -> dict[str, object]:
    return api_response({"status": "ok", "service": settings.PROJECT_NAME})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=api_response(data=None, error=exc.detail, success=False),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=api_response(data=None, error=exc.errors(), success=False),
    )


app.include_router(drains.router)
app.include_router(sensor_data.router)
app.include_router(analysis.router)
app.include_router(dashboard.router)
app.include_router(websocket.router)
