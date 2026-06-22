from .constants import FAKE_YOLO_RESULTS_BY_DRAIN_ID, UNKNOWN_YOLO_RESULT


class FakeYoloPredictor:
    """Deterministic fake YOLO predictor for backend-AI flow tests."""

    def predict(self, drain_id: int) -> dict:
        result = FAKE_YOLO_RESULTS_BY_DRAIN_ID.get(drain_id, UNKNOWN_YOLO_RESULT)
        return dict(result)


def predict_yolo_by_drain_id(drain_id: int) -> dict:
    predictor = FakeYoloPredictor()
    return predictor.predict(drain_id)
