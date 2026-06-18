"""Environment-backed service settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_path(root: Path, raw: str) -> Path:
    path = Path(raw).expanduser()
    return path if path.is_absolute() else (root / path).resolve()


@dataclass(frozen=True)
class Settings:
    project_root: Path
    data_source: str
    mock_data_dir: Path
    model_path: Path
    model_metadata_path: Path
    sensor_lookback_minutes: int
    sensor_short_window_minutes: int
    max_sensor_age_seconds: int
    min_sensor_count_30m: int
    min_yolo_confidence: float
    allow_sensor_danger_override: bool
    database_url: str | None
    log_level: str

    @classmethod
    def from_env(cls, project_root: Path | None = None) -> "Settings":
        root = project_root or Path(__file__).resolve().parents[2]
        load_dotenv(root / ".env", override=False)

        return cls(
            project_root=root,
            data_source=os.getenv("DATA_SOURCE", "mock").strip().lower(),
            mock_data_dir=_resolve_path(root, os.getenv("MOCK_DATA_DIR", "mock_data")),
            model_path=_resolve_path(
                root,
                os.getenv("MODEL_PATH", "models/xgb_mock_baseline.json"),
            ),
            model_metadata_path=_resolve_path(
                root,
                os.getenv("MODEL_METADATA_PATH", "models/model_metadata.json"),
            ),
            sensor_lookback_minutes=int(os.getenv("SENSOR_LOOKBACK_MINUTES", "30")),
            sensor_short_window_minutes=int(
                os.getenv("SENSOR_SHORT_WINDOW_MINUTES", "5")
            ),
            max_sensor_age_seconds=int(os.getenv("MAX_SENSOR_AGE_SECONDS", "300")),
            min_sensor_count_30m=int(os.getenv("MIN_SENSOR_COUNT_30M", "3")),
            min_yolo_confidence=float(os.getenv("MIN_YOLO_CONFIDENCE", "0.15")),
            allow_sensor_danger_override=_as_bool(
                os.getenv("ALLOW_SENSOR_DANGER_OVERRIDE"),
                True,
            ),
            database_url=os.getenv("DATABASE_URL"),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )
