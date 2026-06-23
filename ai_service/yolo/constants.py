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

YOLO_RESULT_FIELDS = (
    "obstruction_ratio",
    "confidence_score",
    "yolo_status",
)

UNKNOWN_YOLO_RESULT = {
    "obstruction_ratio": -1.0,
    "confidence_score": -1.0,
    "yolo_status": YOLO_STATUS_UNKNOWN,
}
