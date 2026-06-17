def run_yolo_analysis(image_url: str | None = None) -> dict[str, float | str | None]:
    """Temporary YOLO stub. Later, load best.pt here and return real detections."""
    return {
        "image_url": image_url,
        "obstruction_ratio": 0.0,
        "confidence_score": 0.0,
        "yolo_status": "unknown",
    }
