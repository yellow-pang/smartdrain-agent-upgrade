import os
from pathlib import Path

from dotenv import load_dotenv

AI_SERVICE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT_DIR = AI_SERVICE_DIR.parent
DEFAULT_IMAGE_SOURCE_BASE_DIR = PROJECT_ROOT_DIR / "mock_data" / "ai_image_samples"

load_dotenv(AI_SERVICE_DIR / ".env")


def _image_source_base_dir() -> Path:
    configured_dir = os.getenv("IMAGE_SOURCE_BASE_DIR")
    if not configured_dir:
        return DEFAULT_IMAGE_SOURCE_BASE_DIR

    path = Path(configured_dir).expanduser()
    if path.is_absolute():
        return path
    return PROJECT_ROOT_DIR / path


IMAGE_SOURCE_BASE_DIR = _image_source_base_dir()

# source_url is a placeholder for a future CCTV/storage source.
# The current local provider only passes local_path to YOLO.
MOCK_IMAGE_SOURCE_BY_DRAIN_ID = {
    1: {
        "source_url": "mock://storage/drain-1-latest.jpg",
        "local_path": str(IMAGE_SOURCE_BASE_DIR / "drain_1.jpg"),
    },
    2: {
        "source_url": "mock://storage/drain-2-latest.jpg",
        "local_path": str(IMAGE_SOURCE_BASE_DIR / "drain_2.jpg"),
    },
    3: {
        "source_url": "mock://storage/drain-3-latest.jpg",
        "local_path": str(IMAGE_SOURCE_BASE_DIR / "drain_3.jpg"),
    },
    4: {
        "source_url": "mock://storage/drain-4-latest.jpg",
        "local_path": str(IMAGE_SOURCE_BASE_DIR / "drain_4.jpg"),
    },
    5: {
        "source_url": "mock://storage/drain-5-latest.jpg",
        "local_path": str(IMAGE_SOURCE_BASE_DIR / "drain_5.jpg"),
    },
}
