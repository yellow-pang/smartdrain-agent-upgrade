FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY ai_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ai_service/ ./ai_service/

RUN useradd --create-home appuser \
    && chown -R appuser:appuser /app

FROM base AS test

USER root
RUN pip install --no-cache-dir pytest
USER appuser
CMD ["python", "-m", "pytest", "ai_service"]

FROM base AS runtime

USER appuser
EXPOSE 9000
CMD ["uvicorn", "ai_service.http.app:app", "--host", "0.0.0.0", "--port", "9000"]
