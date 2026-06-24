import pytest

from ai_service.xgboost.constants import FEATURE_COLUMNS
from ai_service.xgboost.model_predictor import (
    DEFAULT_XGBOOST_MODEL_PATH,
    RISK_LEVEL_BY_LABEL_INDEX,
    TRAINED_MODEL_VERSION,
    TrainedXGBoostPredictor,
    _risk_level_from_label_index,
    validate_label_mapping_covers_risk_levels,
)


def make_batch():
    return {
        "obstruction_ratio": [0.12, 0.65],
        "confidence_score": [0.91, 0.87],
        "water_level": [0.22, 0.54],
        "flow_velocity": [0.81, 0.42],
    }


def test_default_model_path_points_to_ai_service_model_artifact():
    assert DEFAULT_XGBOOST_MODEL_PATH.name == "sewer_xgboost_model.json"
    assert DEFAULT_XGBOOST_MODEL_PATH.parent.name == "model"


def test_label_mapping_matches_training_code_order():
    assert RISK_LEVEL_BY_LABEL_INDEX == {
        0: "good",
        1: "caution",
        2: "danger",
        3: "unknown",
    }
    validate_label_mapping_covers_risk_levels()


def test_unsupported_label_index_raises_value_error():
    with pytest.raises(ValueError):
        _risk_level_from_label_index(99)


def test_predict_batch_returns_existing_contract_shape():
    predictor = TrainedXGBoostPredictor(model=FakeXGBoostModel())

    result = predictor.predict_batch(make_batch())

    assert len(result) == 2
    assert {
        "index",
        "risk_level",
        "risk_score",
        "final_decision",
        "feature_snapshot",
        "model_version",
    }.issubset(result[0])
    assert result[0]["model_version"] == TRAINED_MODEL_VERSION


def test_predict_batch_preserves_feature_order_for_model_input():
    model = FakeXGBoostModel()
    predictor = TrainedXGBoostPredictor(model=model)

    predictor.predict_batch(make_batch())

    assert model.seen_feature_matrices == [
        [[0.12, 0.91, 0.22, 0.81]],
        [[0.65, 0.87, 0.54, 0.42]],
    ]
    assert FEATURE_COLUMNS == [
        "obstruction_ratio",
        "confidence_score",
        "water_level",
        "flow_velocity",
    ]


def test_predict_batch_passes_yolo_unknown_sentinel_to_model():
    model = FakeXGBoostModel()
    predictor = TrainedXGBoostPredictor(model=model)

    predictor.predict_batch(
        {
            "obstruction_ratio": [-1.0],
            "confidence_score": [-1.0],
            "water_level": [0.82],
            "flow_velocity": [0.13],
        }
    )

    assert model.seen_feature_matrices == [[[-1.0, -1.0, 0.82, 0.13]]]


def test_predict_batch_maps_label_and_probability_to_result():
    predictor = TrainedXGBoostPredictor(
        model=FakeXGBoostModel(
            predictions=[2],
            probabilities=[[0.01, 0.04, 0.93, 0.02]],
        )
    )

    result = predictor.predict_batch(
        {
            "obstruction_ratio": [0.88],
            "confidence_score": [0.94],
            "water_level": [0.82],
            "flow_velocity": [0.13],
        }
    )

    assert result[0]["risk_level"] == "danger"
    assert result[0]["final_decision"] == "danger"
    assert result[0]["risk_score"] == 0.93


@pytest.mark.parametrize("value", [None, float("nan")])
def test_none_or_nan_feature_returns_unknown_without_model_call(value):
    model = FakeXGBoostModel()
    predictor = TrainedXGBoostPredictor(model=model)

    result = predictor.predict_batch(
        {
            "obstruction_ratio": [value],
            "confidence_score": [0.94],
            "water_level": [0.82],
            "flow_velocity": [0.13],
        }
    )

    assert result[0]["risk_level"] == "unknown"
    assert result[0]["risk_score"] == 0.0
    assert model.seen_feature_matrices == []


class FakeXGBoostModel:
    def __init__(self, predictions=None, probabilities=None):
        self.predictions = predictions or [0, 1]
        self.probabilities = probabilities or [
            [0.91, 0.04, 0.03, 0.02],
            [0.05, 0.89, 0.04, 0.02],
        ]
        self.call_index = 0
        self.seen_feature_matrices = []

    def predict(self, feature_matrix):
        self.seen_feature_matrices.append(feature_matrix)
        return [self.predictions[self.call_index]]

    def predict_proba(self, feature_matrix):
        probabilities = [self.probabilities[self.call_index]]
        self.call_index += 1
        return probabilities
