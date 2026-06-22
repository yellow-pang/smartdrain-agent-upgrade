from pathlib import Path

AI_SERVICE_DIR = Path(__file__).resolve().parents[1]
SAMPLE_IMAGE_DIR = AI_SERVICE_DIR / "samples"

# source_url은 향후 CCTV/스토리지 GET 연동 시 사용할 자리다.
# 현재 mock 단계에서는 실제로 요청하지 않고, YOLO는 local_path의 로컬 파일만 읽는다.
MOCK_IMAGE_SOURCE_BY_DRAIN_ID = {
    1: {
        "source_url": "mock://storage/drain-1-latest.jpg",
        "local_path": str(SAMPLE_IMAGE_DIR / "drain_1.jpg"),
    },
    2: {
        "source_url": "mock://storage/drain-2-latest.jpg",
        "local_path": str(SAMPLE_IMAGE_DIR / "drain_2.jpg"),
    },
    3: {
        "source_url": "mock://storage/drain-3-latest.jpg",
        "local_path": str(SAMPLE_IMAGE_DIR / "drain_3.jpg"),
    },
    4: {
        "source_url": "mock://storage/drain-4-latest.jpg",
        "local_path": str(SAMPLE_IMAGE_DIR / "drain_4.jpg"),
    },
    5: {
        "source_url": "mock://storage/drain-5-latest.jpg",
        "local_path": str(SAMPLE_IMAGE_DIR / "drain_5.jpg"),
    },
}
