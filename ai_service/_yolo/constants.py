YOLO_STATUS_GOOD = "good"
YOLO_STATUS_DIRTY = "dirty"
YOLO_STATUS_BLOCKED = "blocked"
YOLO_STATUS_UNKNOWN = "unknown"

YOLO_STATUSES = (
    YOLO_STATUS_GOOD,
    YOLO_STATUS_DIRTY,
    YOLO_STATUS_BLOCKED,
    YOLO_STATUS_UNKNOWN,
)

UNKNOWN_YOLO_RESULT = {
    "obstruction_ratio": 0.0,
    "confidence_score": 0.0,
    "yolo_status": YOLO_STATUS_UNKNOWN,
}

FAKE_YOLO_RESULTS_BY_DRAIN_ID = {
    1: {
        "obstruction_ratio": 0.0227,
        "confidence_score": 0.676,
        "yolo_status": YOLO_STATUS_GOOD,
    },
    2: {
        "obstruction_ratio": 0.057,
        "confidence_score": 0.9404,
        "yolo_status": YOLO_STATUS_GOOD,
    },
    3: {
        "obstruction_ratio": 0.002,
        "confidence_score": 0.9371,
        "yolo_status": YOLO_STATUS_GOOD,
    },
    4: {
        "obstruction_ratio": 0.061,
        "confidence_score": 0.8504,
        "yolo_status": YOLO_STATUS_GOOD,
    },
}
