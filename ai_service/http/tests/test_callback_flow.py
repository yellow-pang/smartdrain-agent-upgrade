from ai_service.http import routes
from ai_service.http.config import get_http_settings


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


def make_analysis_result():
    return {
        "accepted_response": {
            "accepted": True,
            "request_id": "REQ_20260618_001",
            "job_id": "AI_JOB_REQ_20260618_001",
            "status": "processing",
        },
        "yolo_callback_payload": {
            "request_id": "REQ_20260618_001",
            "job_id": "AI_JOB_REQ_20260618_001",
            "yolo_result": {
                "obstruction_ratio": 0.057,
                "confidence_score": 0.9404,
                "yolo_status": "good",
            },
        },
        "xgboost_callback_payload": {
            "request_id": "REQ_20260618_001",
            "job_id": "AI_JOB_REQ_20260618_001",
            "xgboost_result": {
                "risk_score": 0.65,
                "risk_level": "caution",
                "final_decision": "monitoring",
                "evaluated_at": "2026-06-19T13:30:00+09:00",
            },
        },
    }


def test_process_analysis_callbacks_sends_yolo_and_xgboost_payloads(monkeypatch):
    sent_callbacks = []
    analysis_result = make_analysis_result()

    monkeypatch.setenv("BACKEND_BASE_URL", "http://backend.example:8000")
    monkeypatch.setattr(
        routes,
        "run_analysis_job",
        lambda payload: analysis_result,
    )

    def fake_send_json_callback(url, payload, timeout_seconds, retry_count):
        sent_callbacks.append((url, payload, timeout_seconds, retry_count))
        return True

    monkeypatch.setattr(routes, "send_json_callback", fake_send_json_callback)

    routes.process_analysis_callbacks(make_payload())

    assert sent_callbacks == [
        (
            "http://backend.example:8000/api/ai-callback/yolo-result",
            analysis_result["yolo_callback_payload"],
            10.0,
            1,
        ),
        (
            "http://backend.example:8000/api/ai-callback/xgboost-result",
            analysis_result["xgboost_callback_payload"],
            10.0,
            1,
        ),
    ]


def test_process_analysis_callbacks_continues_after_yolo_callback_failure(
    monkeypatch,
):
    sent_urls = []

    monkeypatch.setattr(
        routes,
        "run_analysis_job",
        lambda payload: make_analysis_result(),
    )

    def fake_send_json_callback(url, payload, timeout_seconds, retry_count):
        sent_urls.append(url)
        return "xgboost-result" in url

    monkeypatch.setattr(routes, "send_json_callback", fake_send_json_callback)

    routes.process_analysis_callbacks(make_payload())

    assert sent_urls == [
        "http://localhost:8000/api/ai-callback/yolo-result",
        "http://localhost:8000/api/ai-callback/xgboost-result",
    ]


def test_process_analysis_callbacks_does_not_send_callbacks_when_analysis_fails(
    monkeypatch,
):
    sent_callbacks = []

    def fake_run_analysis_job(payload):
        raise RuntimeError("analysis failed")

    monkeypatch.setattr(routes, "run_analysis_job", fake_run_analysis_job)
    monkeypatch.setattr(
        routes,
        "send_json_callback",
        lambda *args: sent_callbacks.append(args),
    )

    routes.process_analysis_callbacks(make_payload())

    assert sent_callbacks == []


def test_backend_base_url_environment_variable_changes_callback_urls(monkeypatch):
    monkeypatch.setenv("BACKEND_BASE_URL", "http://backend.example:8000/")

    settings = get_http_settings()

    assert settings.backend_base_url == "http://backend.example:8000"
    assert (
        settings.yolo_callback_url
        == "http://backend.example:8000/api/ai-callback/yolo-result"
    )
    assert (
        settings.xgboost_callback_url
        == "http://backend.example:8000/api/ai-callback/xgboost-result"
    )
