import pytest

from ai_service.xgboost import service as xgboost_service
from ai_service.xgboost.constants import FEATURE_COLUMNS
from ai_service.xgboost.service import predict_flood_risk_batch
from ai_service.xgboost.validator import validate_input_batch


def make_batch():
    return {
        "obstruction_ratio": [0.12, 0.65, 0.88],
        "confidence_score": [0.91, 0.87, 0.94],
        "water_level": [0.22, 0.54, 0.82],
        "flow_velocity": [0.81, 0.42, 0.13],
    }


class FakeTrainedXGBoostPredictor:
    def predict_batch(self, input_dict_batch):
        validate_input_batch(input_dict_batch)
        row_count = len(input_dict_batch["obstruction_ratio"])
        return [
            {
                "index": index,
                "risk_level": "good",
                "risk_score": 0.91,
                "final_decision": "good",
                "feature_snapshot": {
                    column: input_dict_batch[column][index]
                    for column in FEATURE_COLUMNS
                },
                "model_version": "test_trained_xgb",
            }
            for index in range(row_count)
        ]


@pytest.fixture(autouse=True)
def stub_trained_predictor(monkeypatch):
    monkeypatch.setattr(
        xgboost_service,
        "TrainedXGBoostPredictor",
        lambda: FakeTrainedXGBoostPredictor(),
    )


def test_predict_returns_list_for_valid_batch():
    result = predict_flood_risk_batch(make_batch())

    assert isinstance(result, list)
    assert len(result) == 3


def test_result_contains_required_keys():
    result = predict_flood_risk_batch(make_batch())

    assert {
        "index",
        "risk_level",
        "risk_score",
        "final_decision",
        "feature_snapshot",
        "model_version",
    }.issubset(result[0])
    assert result[0]["model_version"] == "test_trained_xgb"


def test_mismatched_list_lengths_raise_value_error():
    batch = make_batch()
    batch["flow_velocity"] = [0.81]

    with pytest.raises(ValueError):
        predict_flood_risk_batch(batch)


def test_missing_required_key_raises_value_error():
    batch = make_batch()
    del batch["water_level"]

    with pytest.raises(ValueError):
        predict_flood_risk_batch(batch)


def test_single_row_batch_is_supported():
    batch = {
        "obstruction_ratio": [0.12],
        "confidence_score": [0.91],
        "water_level": [0.22],
        "flow_velocity": [0.81],
    }

    result = predict_flood_risk_batch(batch)

    assert len(result) == 1
    assert result[0]["index"] == 0
    assert result[0]["risk_level"] == "good"


def test_multi_row_output_preserves_input_order_and_index():
    result = predict_flood_risk_batch(make_batch())

    assert [row["index"] for row in result] == [0, 1, 2]
    assert result[0]["feature_snapshot"]["obstruction_ratio"] == 0.12
    assert result[1]["feature_snapshot"]["obstruction_ratio"] == 0.65
    assert result[2]["feature_snapshot"]["obstruction_ratio"] == 0.88
