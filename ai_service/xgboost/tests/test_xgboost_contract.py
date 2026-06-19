import pytest

from ai_service.xgboost.constants import MODEL_VERSION
from ai_service.xgboost.service import predict_flood_risk_batch


def make_batch():
    return {
        "obstruction_ratio": [0.12, 0.65, 0.88],
        "confidence_score": [0.91, 0.87, 0.94],
        "water_level": [0.22, 0.54, 0.82],
        "flow_velocity": [0.81, 0.42, 0.13],
    }


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
    assert result[0]["model_version"] == MODEL_VERSION


def test_low_confidence_row_is_unknown():
    batch = {
        "obstruction_ratio": [0.12],
        "confidence_score": [0.49],
        "water_level": [0.22],
        "flow_velocity": [0.81],
    }

    result = predict_flood_risk_batch(batch)

    assert result[0]["risk_level"] == "unknown"
    assert result[0]["final_decision"] == "unknown"
    assert result[0]["risk_score"] == 0.0


@pytest.mark.parametrize("value", [None, float("nan")])
def test_none_or_nan_row_value_is_unknown(value):
    batch = {
        "obstruction_ratio": [value],
        "confidence_score": [0.91],
        "water_level": [0.22],
        "flow_velocity": [0.81],
    }

    result = predict_flood_risk_batch(batch)

    assert result[0]["risk_level"] == "unknown"


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

