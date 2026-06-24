from pathlib import Path

from ai_service.yolo.analyzer import (
    DEFAULT_YOLO_MODEL_PATH,
    YoloV3ImageAnalyzer,
    _classify_yolo_status,
    _percent_to_unit_ratio,
)
from ai_service.yolo.constants import UNKNOWN_YOLO_RESULT


def test_default_model_path_points_to_ai_service_model_best_pt():
    assert DEFAULT_YOLO_MODEL_PATH == (
        Path(__file__).resolve().parents[2] / "model" / "best.pt"
    )


def test_percent_to_unit_ratio_converts_and_clamps():
    assert _percent_to_unit_ratio(57.2) == 0.572
    assert _percent_to_unit_ratio(-5) == 0.0
    assert _percent_to_unit_ratio(125) == 1.0


def test_classify_yolo_status_from_obstruction_ratio():
    assert _classify_yolo_status(0.0) == "good"
    assert _classify_yolo_status(0.2999) == "good"
    assert _classify_yolo_status(0.30) == "dirty"
    assert _classify_yolo_status(0.75) == "blocked"


def test_image_read_failure_returns_unknown_result():
    analyzer = YoloV3ImageAnalyzer(
        model=object(),
        cv2_module=FailingCv2(),
        np_module=FakeNp(),
    )

    assert analyzer.analyze_image("missing.jpg") == UNKNOWN_YOLO_RESULT


def test_missing_drain_detection_returns_unknown_result():
    analyzer = AnalyzerWithPreparedImage(
        model=FakeModel([FakeBox(class_id=0, confidence=0.91, coords=[1, 1, 4, 4])])
    )

    assert analyzer.analyze_image("image.jpg") == UNKNOWN_YOLO_RESULT


def test_successful_detection_returns_yolo_contract(monkeypatch):
    analyzer = AnalyzerWithPreparedImage(
        model=FakeModel(
            [
                FakeBox(class_id=1, confidence=0.94, coords=[0, 0, 10, 10]),
                FakeBox(class_id=0, confidence=0.88, coords=[0, 0, 5, 6]),
            ]
        )
    )

    monkeypatch.setattr(
        analyzer,
        "_calculate_obstruction_metrics",
        lambda _original_img, _drain_box, _debris_boxes: {
            "total_obstruction_ratio": 57.2,
            "debris_ratio": 30.0,
            "soil_ratio": 38.86,
        },
    )

    assert analyzer.analyze_image("image.jpg") == {
        "obstruction_ratio": 0.572,
        "confidence_score": 0.94,
        "yolo_status": "dirty",
    }


class AnalyzerWithPreparedImage(YoloV3ImageAnalyzer):
    def __init__(self, model):
        super().__init__(model=model)

    def preprocess_image(self, image_path):
        return object(), object()


class FakeModel:
    def __init__(self, boxes):
        self.boxes = boxes

    def predict(self, processed_img, conf, verbose):
        return [FakePredictionResult(self.boxes)]


class FakePredictionResult:
    def __init__(self, boxes):
        self.boxes = boxes


class FakeBox:
    def __init__(self, class_id, confidence, coords):
        self.cls = [class_id]
        self.conf = [confidence]
        self.xyxy = [FakeCoords(coords)]


class FakeCoords:
    def __init__(self, coords):
        self.coords = coords

    def tolist(self):
        return list(self.coords)


class FailingCv2:
    IMREAD_COLOR = 1

    def imdecode(self, img_array, flags):
        return None


class FakeNp:
    uint8 = "uint8"

    def fromfile(self, image_path, dtype):
        return b""
