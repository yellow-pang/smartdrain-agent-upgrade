"""
YOLO 분석 전 이미지 전처리 진입점을 제공하는 파일입니다.

주요 역할:
- 이미지 경로 입력을 받아 전처리 함수 호출 형태 제공
- 입력 이미지가 없을 때 None 반환
"""

import numpy as np


def preprocess_image(image_path: str | None) -> np.ndarray | None:
    """Placeholder for OpenCV preprocessing before YOLO inference."""
    if not image_path:
        return None
    return None
