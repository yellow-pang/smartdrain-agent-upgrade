import pytest

from ai_service.yolo.constants import YOLO_STATUSES
from ai_service.analysis import service as analysis_service
from ai_service.analysis.callback_payloads import (
    build_xgboost_callback_payload,
    build_yolo_callback_payload,
)
from ai_service.analysis.decision_mapper import (
    BACKEND_FINAL_DECISION_BY_RISK_LEVEL,
)
from ai_service.analysis.job_id import build_job_id
from ai_service.analysis.service import run_analysis_job
from ai_service.xgboost.constants import RISK_LEVELS


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
            "feature_snapshot": {},
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


class FakeImageSource:
    def __init__(self, source_url, local_path):
        self.source_url = source_url
        self.local_path = local_path


def test_job_id_policy_is_request_id_based():
    assert build_job_id("REQ_20260618_001") == "AI_JOB_REQ_20260618_001"


def test_async_contract_returns_three_payload_groups():
    result = run_analysis_job(make_payload())

    assert set(result) == {
        "accepted_response",
        "yolo_callback_payload",
        "xgboost_callback_payload",
    }


def test_callback_payloads_do_not_include_drain_id():
    result = run_analysis_job(make_payload())

    assert "drain_id" not in result["yolo_callback_payload"]
    assert "drain_id" not in result["xgboost_callback_payload"]


def test_yolo_callback_contract_fields_are_fixed():
    yolo_result = {
        "obstruction_ratio": 0.057,
        "confidence_score": 0.9404,
        "yolo_status": "good",
    }

    payload = build_yolo_callback_payload(
        "REQ_20260618_001",
        "AI_JOB_REQ_20260618_001",
        yolo_result,
    )

    assert set(payload) == {"request_id", "job_id", "yolo_result"}
    assert set(payload["yolo_result"]) == {
        "obstruction_ratio",
        "confidence_score",
        "yolo_status",
    }
    assert payload["yolo_result"]["yolo_status"] in YOLO_STATUSES


def test_xgboost_callback_contract_fields_are_fixed():
    xgboost_result = {
        "risk_score": 0.65,
        "risk_level": "caution",
    }

    payload = build_xgboost_callback_payload(
        "REQ_20260618_001",
        "AI_JOB_REQ_20260618_001",
        xgboost_result,
        "2026-06-19T13:30:00+09:00",
    )

    assert set(payload) == {"request_id", "job_id", "xgboost_result"}
    assert set(payload["xgboost_result"]) == {
        "risk_score",
        "risk_level",
        "final_decision",
        "evaluated_at",
    }
    assert payload["xgboost_result"]["risk_level"] in RISK_LEVELS
    assert (
        payload["xgboost_result"]["final_decision"]
        in BACKEND_FINAL_DECISION_BY_RISK_LEVEL.values()
    )


def test_unknown_is_allowed_yolo_status():
    assert "unknown" in YOLO_STATUSES


def test_backend_final_decision_mapping_covers_all_risk_levels():
    assert set(BACKEND_FINAL_DECISION_BY_RISK_LEVEL) == set(RISK_LEVELS)
