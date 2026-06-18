"""
YOLO 이미지 분석 함수 형태를 제공하는 파일입니다.

주요 역할:
- 이미지 URL을 입력받는 분석 함수 제공
- 기본 막힘 비율, 신뢰도, 상태 값을 반환
"""

def run_yolo_analysis(image_url: str | None = None) -> dict[str, float | str | None]:
    """Temporary YOLO stub. Later, load best.pt here and return real detections."""
    return {
        "image_url": image_url,
        "obstruction_ratio": 0.0,
        "confidence_score": 0.0,
        "yolo_status": "unknown",
    }
