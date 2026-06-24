from fastapi import FastAPI

from .routes import router

app = FastAPI(title="SmartDrain AI Service")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(router)
