import pytest
from fastapi import HTTPException

from ai_service.http import routes


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


class FakeBackgroundTasks:
    def __init__(self):
        self.calls = []

    def add_task(self, task_func, *args, **kwargs):
        self.calls.append((task_func, args, kwargs))


def test_analysis_endpoint_returns_accepted_response(monkeypatch):
    calls = []

    def fake_process_analysis_callbacks(payload):
        calls.append(payload)

    monkeypatch.setattr(
        routes,
        "process_analysis_callbacks",
        fake_process_analysis_callbacks,
    )

    background_tasks = FakeBackgroundTasks()
    response = routes.run_analysis(make_payload(), background_tasks)

    assert response == {
        "accepted": True,
        "request_id": "REQ_20260618_001",
        "job_id": "AI_JOB_REQ_20260618_001",
        "status": "processing",
    }
    assert background_tasks.calls == [
        (fake_process_analysis_callbacks, (make_payload(),), {})
    ]
    assert calls == []


def test_analysis_endpoint_returns_400_for_invalid_payload():
    payload = make_payload()
    del payload["request_id"]

    with pytest.raises(HTTPException) as exc_info:
        routes.run_analysis(payload, FakeBackgroundTasks())

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["error"]["code"] == "INVALID_INPUT"


def test_analysis_endpoint_returns_400_for_unconfigured_drain_id():
    payload = make_payload()
    payload["drain_id"] = 999

    with pytest.raises(HTTPException) as exc_info:
        routes.run_analysis(payload, FakeBackgroundTasks())

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["error"]["code"] == "INVALID_INPUT"
    assert "drain_id" in exc_info.value.detail["error"]["message"]
