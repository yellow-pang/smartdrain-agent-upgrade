import pytest

from ai_service.yolo.constants import (
    UNKNOWN_YOLO_RESULT,
    YOLO_RESULT_FIELDS,
    YOLO_STATUSES,
    YOLO_STATUS_BLOCKED,
    YOLO_STATUS_DIRTY,
    YOLO_STATUS_GOOD,
    YOLO_STATUS_UNKNOWN,
)
from ai_service.yolo.contract import validate_yolo_result_contract


def test_yolo_statuses_are_fixed_contract_values():
    assert YOLO_STATUSES == (
        YOLO_STATUS_GOOD,
        YOLO_STATUS_DIRTY,
        YOLO_STATUS_BLOCKED,
        YOLO_STATUS_UNKNOWN,
    )


def test_yolo_result_fields_are_fixed_contract_values():
    assert YOLO_RESULT_FIELDS == (
        "obstruction_ratio",
        "confidence_score",
        "yolo_status",
    )


def test_unknown_yolo_result_matches_contract():
    validate_yolo_result_contract(UNKNOWN_YOLO_RESULT)
    assert UNKNOWN_YOLO_RESULT == {
        "obstruction_ratio": -1.0,
        "confidence_score": -1.0,
        "yolo_status": "unknown",
    }


def test_valid_yolo_result_contract_passes():
    validate_yolo_result_contract(
        {
            "obstruction_ratio": 0.057,
            "confidence_score": 0.9404,
            "yolo_status": "good",
        }
    )


def test_missing_yolo_result_field_raises_value_error():
    with pytest.raises(ValueError):
        validate_yolo_result_contract(
            {
                "obstruction_ratio": 0.057,
                "confidence_score": 0.9404,
            }
        )


def test_unsupported_yolo_status_raises_value_error():
    with pytest.raises(ValueError):
        validate_yolo_result_contract(
            {
                "obstruction_ratio": 0.057,
                "confidence_score": 0.9404,
                "yolo_status": "unsupported",
            }
        )


@pytest.mark.parametrize(
    "result",
    [
        {
            "obstruction_ratio": 0.0,
            "confidence_score": -1.0,
            "yolo_status": "unknown",
        },
        {
            "obstruction_ratio": -1.0,
            "confidence_score": 0.0,
            "yolo_status": "unknown",
        },
    ],
)
def test_unknown_yolo_status_requires_sentinel_values(result):
    with pytest.raises(ValueError):
        validate_yolo_result_contract(result)


@pytest.mark.parametrize(
    "result",
    [
        {
            "obstruction_ratio": -1.0,
            "confidence_score": 0.9404,
            "yolo_status": "good",
        },
        {
            "obstruction_ratio": 0.057,
            "confidence_score": -1.0,
            "yolo_status": "dirty",
        },
    ],
)
def test_non_unknown_yolo_status_rejects_sentinel_values(result):
    with pytest.raises(ValueError):
        validate_yolo_result_contract(result)


@pytest.mark.parametrize(
    "field_name",
    [
        "obstruction_ratio",
        "confidence_score",
    ],
)
@pytest.mark.parametrize(
    "value",
    ["bad", "0.5", None, {}, True, float("nan"), float("inf")],
)
def test_yolo_numeric_fields_must_be_finite_numbers(field_name, value):
    result = {
        "obstruction_ratio": 0.057,
        "confidence_score": 0.9404,
        "yolo_status": "good",
    }
    result[field_name] = value

    with pytest.raises(ValueError):
        validate_yolo_result_contract(result)


@pytest.mark.parametrize(
    "field_name",
    [
        "obstruction_ratio",
        "confidence_score",
    ],
)
@pytest.mark.parametrize("value", [-0.0001, 1.0001])
def test_yolo_numeric_fields_must_be_unit_range_for_normal_status(
    field_name,
    value,
):
    result = {
        "obstruction_ratio": 0.057,
        "confidence_score": 0.9404,
        "yolo_status": "good",
    }
    result[field_name] = value

    with pytest.raises(ValueError):
        validate_yolo_result_contract(result)
