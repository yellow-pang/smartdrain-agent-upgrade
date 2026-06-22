import re

import pytest

from ai_service.analysis.decision_mapper import map_risk_level_to_backend_decision
from ai_service.analysis import service as analysis_service
from ai_service.analysis.service import run_analysis_job
from ai_service.analysis.xgboost_adapter import build_xgboost_input_batch


def make_payload():
    return {
        "request_id": "REQ_20260618_001",
        "drain_id": 2,
        "sensor_data": {
            "measured_at": "2026-06-18T08:36:13+09:00",
            "water_level_cm": 98.13,
            "flow_velocity_mps": 0.4512,
            "quality_status": "valid",
        },
    }


def fake_yolo_result(image_path):
    return {
        "obstruction_ratio": 0.057,
        "confidence_score": 0.9404,
        "yolo_status": "good",
    }


def fake_xgboost_result(input_dict_batch):
    return [
        {
            "index": 0,
            "risk_score": 0.65,
            "risk_level": "caution",
            "final_decision": "caution",
            "feature_snapshot": {
                "obstruction_ratio": input_dict_batch["obstruction_ratio"][0],
                "confidence_score": input_dict_batch["confidence_score"][0],
                "water_level": input_dict_batch["water_level"][0],
                "flow_velocity": input_dict_batch["flow_velocity"][0],
            },
            "model_version": "test_xgb",
        }
    ]


@pytest.fixture(autouse=True)
def stub_model_predictors(monkeypatch):
    monkeypatch.setattr(
        analysis_service,
        "resolve_image_source_by_drain_id",
        lambda drain_id: FakeImageSource(
            source_url=f"mock://storage/drain-{drain_id}-latest.jpg",
            local_path=f"ai_service/samples/drain_{drain_id}.jpg",
        ),
    )
    monkeypatch.setattr(analysis_service, "predict_yolo_by_image_path", fake_yolo_result)
    monkeypatch.setattr(analysis_service, "predict_flood_risk_batch", fake_xgboost_result)


def test_run_analysis_job_returns_accepted_response():
    result = run_analysis_job(make_payload())

    assert result["accepted_response"] == {
        "accepted": True,
        "request_id": "REQ_20260618_001",
        "job_id": "AI_JOB_REQ_20260618_001",
        "status": "processing",
    }


def test_request_id_and_job_id_are_preserved_in_callbacks():
    result = run_analysis_job(make_payload())

    assert result["yolo_callback_payload"]["request_id"] == "REQ_20260618_001"
    assert result["yolo_callback_payload"]["job_id"] == "AI_JOB_REQ_20260618_001"
    assert result["xgboost_callback_payload"]["request_id"] == "REQ_20260618_001"
    assert result["xgboost_callback_payload"]["job_id"] == "AI_JOB_REQ_20260618_001"


def test_yolo_callback_payload_matches_contract():
    result = run_analysis_job(make_payload())

    assert result["yolo_callback_payload"] == {
        "request_id": "REQ_20260618_001",
        "job_id": "AI_JOB_REQ_20260618_001",
        "yolo_result": {
            "obstruction_ratio": 0.057,
            "confidence_score": 0.9404,
            "yolo_status": "good",
        },
    }


def test_xgboost_callback_payload_matches_contract():
    result = run_analysis_job(make_payload())
    xgboost_result = result["xgboost_callback_payload"]["xgboost_result"]

    assert {"risk_score", "risk_level", "final_decision", "evaluated_at"}.issubset(
        xgboost_result
    )
    assert xgboost_result["risk_level"] == "caution"
    assert xgboost_result["final_decision"] == "monitoring"
    assert re.match(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
        xgboost_result["evaluated_at"],
    )
    assert xgboost_result["evaluated_at"].endswith("+09:00")


def test_run_analysis_job_resolves_image_source_from_drain_id(monkeypatch):
    seen_drain_ids = []
    seen_image_paths = []

    def spy_image_source(drain_id):
        seen_drain_ids.append(drain_id)
        return FakeImageSource(
            source_url=f"mock://storage/drain-{drain_id}-latest.jpg",
            local_path=f"ai_service/samples/drain_{drain_id}.jpg",
        )

    def spy_yolo_result(image_path):
        seen_image_paths.append(image_path)
        return fake_yolo_result(image_path)

    monkeypatch.setattr(analysis_service, "resolve_image_source_by_drain_id", spy_image_source)
    monkeypatch.setattr(analysis_service, "predict_yolo_by_image_path", spy_yolo_result)

    run_analysis_job(make_payload())

    assert seen_drain_ids == [2]
    assert seen_image_paths == ["ai_service/samples/drain_2.jpg"]


@pytest.mark.parametrize(
    ("risk_level", "expected_decision"),
    [
        ("good", "normal"),
        ("caution", "monitoring"),
        ("danger", "dispatch_required"),
        ("unknown", "field_check"),
    ],
)
def test_risk_level_maps_to_backend_final_decision(
    risk_level,
    expected_decision,
):
    assert map_risk_level_to_backend_decision(risk_level) == expected_decision


def test_missing_required_payload_key_raises_value_error():
    payload = make_payload()
    del payload["request_id"]

    with pytest.raises(ValueError):
        run_analysis_job(payload)


def test_invalid_quality_status_raises_value_error():
    payload = make_payload()
    payload["sensor_data"]["quality_status"] = "invalid"

    with pytest.raises(ValueError):
        run_analysis_job(payload)


def test_xgboost_adapter_normalizes_sensor_units():
    sensor_data = {
        "water_level_cm": 98.13,
        "flow_velocity_mps": 0.4512,
    }
    yolo_result = {
        "obstruction_ratio": 0.057,
        "confidence_score": 0.9404,
    }

    result = build_xgboost_input_batch(sensor_data, yolo_result)

    assert result == {
        "obstruction_ratio": [0.057],
        "confidence_score": [0.9404],
        "water_level": [0.9813],
        "flow_velocity": [0.4512],
    }


class FakeImageSource:
    def __init__(self, source_url, local_path):
        self.source_url = source_url
        self.local_path = local_path
