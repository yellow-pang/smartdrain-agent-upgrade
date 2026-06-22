from pathlib import Path

from .constants import (
    UNKNOWN_YOLO_RESULT,
    YOLO_STATUS_BLOCKED,
    YOLO_STATUS_DIRTY,
    YOLO_STATUS_GOOD,
)
from .contract import validate_yolo_result_contract

AI_SERVICE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_YOLO_MODEL_PATH = AI_SERVICE_DIR / "model" / "best.pt"

DEBRIS_CLASS_ID = 0
DRAIN_CLASS_ID = 1
DEFAULT_CONFIDENCE_THRESHOLD = 0.25
DEFAULT_SHADOW_THRESHOLD = 45


class YoloV3ImageAnalyzer:
    """YOLOv8 + OpenCV analyzer adapted from the V3 PoC pipeline."""

    def __init__(
        self,
        model_path: str | Path | None = None,
        model=None,
        cv2_module=None,
        np_module=None,
    ):
        self.model_path = Path(model_path or DEFAULT_YOLO_MODEL_PATH)
        self.model = model if model is not None else self._load_yolo_model()
        self.cv2 = cv2_module
        self.np = np_module

    def analyze_image(self, image_path: str | Path) -> dict:
        original_img, processed_img = self.preprocess_image(image_path)
        if processed_img is None:
            return dict(UNKNOWN_YOLO_RESULT)

        try:
            results = self.model.predict(
                processed_img,
                conf=DEFAULT_CONFIDENCE_THRESHOLD,
                verbose=False,
            )
            boxes = results[0].boxes
        except Exception:
            return dict(UNKNOWN_YOLO_RESULT)

        drain_box, drain_confidence, debris_boxes = self._split_detection_boxes(boxes)
        if drain_box is None:
            return dict(UNKNOWN_YOLO_RESULT)

        metrics = self._calculate_obstruction_metrics(
            original_img,
            drain_box,
            debris_boxes,
        )
        if metrics is None:
            return dict(UNKNOWN_YOLO_RESULT)

        # PoC V3 계산값은 percent(0~100)였지만 XGBoost 입력 contract는 ratio(0~1)다.
        # 이 변환을 빠뜨리면 학습 때의 feature scale과 달라져 위험도 예측이 왜곡된다.
        obstruction_ratio = _percent_to_unit_ratio(metrics["total_obstruction_ratio"])
        result = {
            "obstruction_ratio": obstruction_ratio,
            "confidence_score": round(_clamp_unit(drain_confidence), 4),
            "yolo_status": _classify_yolo_status(obstruction_ratio),
        }
        validate_yolo_result_contract(result)
        return result

    def preprocess_image(self, image_path: str | Path):
        cv2, np = self._get_cv2_np()

        try:
            img_array = np.fromfile(str(image_path), np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        except Exception:
            return None, None

        if img is None:
            return None, None

        original_img = img.copy()
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced_l = clahe.apply(l_channel)
        enhanced_lab = cv2.merge((enhanced_l, a_channel, b_channel))
        enhanced_img = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

        return original_img, enhanced_img

    def _calculate_obstruction_metrics(
        self,
        original_img,
        drain_box: list[float],
        debris_boxes: list[tuple[list[float], float]],
    ) -> dict | None:
        cv2, np = self._get_cv2_np()

        dr_x1, dr_y1, dr_x2, dr_y2 = map(int, drain_box)
        drain_width = dr_x2 - dr_x1
        drain_height = dr_y2 - dr_y1
        drain_area = drain_width * drain_height
        if drain_area <= 0:
            return None

        valid_debris_area = 0.0
        for debris_box, _confidence in debris_boxes:
            d_x1, d_y1, d_x2, d_y2 = map(int, debris_box)
            center_x = (d_x1 + d_x2) / 2
            center_y = (d_y1 + d_y2) / 2
            # debris box 중심이 drain 영역 안에 있을 때만 막힘 면적으로 반영한다.
            # 화면 바깥 쓰레기 탐지가 하수구 막힘률에 섞이는 것을 막기 위한 기준이다.
            if dr_x1 <= center_x <= dr_x2 and dr_y1 <= center_y <= dr_y2:
                valid_debris_area += max(d_x2 - d_x1, 0) * max(d_y2 - d_y1, 0)

        drain_crop = original_img[dr_y1:dr_y2, dr_x1:dr_x2]
        if getattr(drain_crop, "size", 0) == 0:
            return None

        hsv_crop = cv2.cvtColor(drain_crop, cv2.COLOR_BGR2HSV)
        hsv_params = _default_hsv_params(np)
        mask1 = cv2.inRange(hsv_crop, hsv_params["lower1"], hsv_params["upper1"])
        mask2 = cv2.inRange(hsv_crop, hsv_params["lower2"], hsv_params["upper2"])
        dirt_mask = cv2.bitwise_or(mask1, mask2)

        # 어두운 구멍/그림자는 흙 막힘으로 오인되기 쉬워 soil mask에서 제외한다.
        lower_dark = np.array([0, 0, 0])
        upper_dark = np.array([179, 255, DEFAULT_SHADOW_THRESHOLD])
        dark_hole_mask = cv2.inRange(hsv_crop, lower_dark, upper_dark)
        dirt_mask = cv2.bitwise_and(dirt_mask, cv2.bitwise_not(dark_hole_mask))

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dirt_mask = cv2.dilate(dirt_mask, kernel, iterations=2)
        dirt_mask = cv2.morphologyEx(dirt_mask, cv2.MORPH_OPEN, kernel)

        dirt_area = cv2.countNonZero(dirt_mask)
        debris_ratio = (valid_debris_area / drain_area) * 100.0
        soil_ratio = (dirt_area / drain_area) * 100.0
        total_obstruction_ratio = (
            debris_ratio + soil_ratio - ((debris_ratio * soil_ratio) / 100.0)
        )

        return {
            "total_obstruction_ratio": round(total_obstruction_ratio, 2),
            "debris_ratio": round(debris_ratio, 2),
            "soil_ratio": round(soil_ratio, 2),
        }

    def _split_detection_boxes(self, boxes) -> tuple[list[float] | None, float, list]:
        drain_box = None
        drain_confidence = 0.0
        debris_boxes = []

        for box in boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            coords = box.xyxy[0].tolist()

            if class_id == DRAIN_CLASS_ID and confidence > drain_confidence:
                drain_box = coords
                drain_confidence = confidence
            elif class_id == DEBRIS_CLASS_ID:
                debris_boxes.append((coords, confidence))

        return drain_box, drain_confidence, debris_boxes

    def _load_yolo_model(self):
        from ultralytics import YOLO

        return YOLO(str(self.model_path))

    def _get_cv2_np(self):
        if self.cv2 is None:
            import cv2

            self.cv2 = cv2
        if self.np is None:
            import numpy as np

            self.np = np
        return self.cv2, self.np


def predict_yolo_by_image_path(image_path: str | Path) -> dict:
    return YoloV3ImageAnalyzer().analyze_image(image_path)


def _default_hsv_params(np) -> dict:
    return {
        "lower1": np.array([10, 40, 20]),
        "upper1": np.array([35, 255, 200]),
        "lower2": np.array([0, 20, 10]),
        "upper2": np.array([10, 200, 150]),
    }


def _percent_to_unit_ratio(value: float) -> float:
    # YOLO 내부 계산은 percent지만 외부 contract와 XGBoost feature는 unit ratio다.
    return round(_clamp_unit(float(value) / 100.0), 4)


def _clamp_unit(value: float) -> float:
    return min(max(float(value), 0.0), 1.0)


def _classify_yolo_status(obstruction_ratio: float) -> str:
    if obstruction_ratio >= 0.75:
        return YOLO_STATUS_BLOCKED
    if obstruction_ratio >= 0.30:
        return YOLO_STATUS_DIRTY
    return YOLO_STATUS_GOOD
