from fastapi import FastAPI

from .routes import router

app = FastAPI(title="SmartDrain AI Service")
app.include_router(router)

