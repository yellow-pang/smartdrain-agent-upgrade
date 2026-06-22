import builtins

import pytest

from ai_service.yolo_legacy_example.constants import YOLO_STATUSES
from ai_service.yolo_legacy_example.fake_yolo_predictor import FakeYoloPredictor


EXPECTED_RESULTS = {
    1: {
        "obstruction_ratio": 0.0227,
        "confidence_score": 0.676,
        "yolo_status": "good",
    },
    2: {
        "obstruction_ratio": 0.057,
        "confidence_score": 0.9404,
        "yolo_status": "good",
    },
    3: {
        "obstruction_ratio": 0.002,
        "confidence_score": 0.9371,
        "yolo_status": "good",
    },
    4: {
        "obstruction_ratio": 0.061,
        "confidence_score": 0.8504,
        "yolo_status": "good",
    },
}


def test_supported_drain_id_returns_dict_result():
    predictor = FakeYoloPredictor()

    result = predictor.predict(1)

    assert isinstance(result, dict)


def test_result_contains_required_keys():
    predictor = FakeYoloPredictor()

    result = predictor.predict(1)

    assert {"obstruction_ratio", "confidence_score", "yolo_status"}.issubset(result)


def test_yolo_status_is_allowed_value():
    predictor = FakeYoloPredictor()

    result = predictor.predict(1)

    assert result["yolo_status"] in YOLO_STATUSES


def test_same_drain_id_returns_same_result():
    predictor = FakeYoloPredictor()

    first_result = predictor.predict(2)
    second_result = predictor.predict(2)

    assert first_result == second_result


@pytest.mark.parametrize("drain_id, expected", EXPECTED_RESULTS.items())
def test_supported_drain_ids_return_expected_mock_values(drain_id, expected):
    predictor = FakeYoloPredictor()

    result = predictor.predict(drain_id)

    assert result == expected


def test_unknown_drain_id_returns_unknown_result():
    predictor = FakeYoloPredictor()

    result = predictor.predict(999)

    assert result == {
        "obstruction_ratio": 0.0,
        "confidence_score": 0.0,
        "yolo_status": "unknown",
    }


def test_fake_yolo_does_not_depend_on_external_files(monkeypatch):
    def fail_open(*args, **kwargs):
        raise AssertionError("Fake YOLO should not read external files.")

    monkeypatch.setattr(builtins, "open", fail_open)
    predictor = FakeYoloPredictor()

    result = predictor.predict(1)

    assert result == EXPECTED_RESULTS[1]
