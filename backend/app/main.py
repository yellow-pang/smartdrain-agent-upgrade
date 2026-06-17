from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import analysis, dashboard, drains, sensor_data, websocket


app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.PROJECT_NAME}


app.include_router(drains.router)
app.include_router(sensor_data.router)
app.include_router(analysis.router)
app.include_router(dashboard.router)
app.include_router(websocket.router)
