import logging
from urllib import error

from ai_service.http import callback_sender


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return b""


def test_send_json_callback_returns_true_on_success(monkeypatch):
    calls = []

    def fake_urlopen(req, timeout):
        calls.append((req, timeout))
        return FakeResponse()

    monkeypatch.setattr(callback_sender.request, "urlopen", fake_urlopen)

    result = callback_sender.send_json_callback(
        "http://localhost:8000/api/ai-callback/yolo-result",
        {"ok": True},
        timeout_seconds=10,
        retry_count=1,
    )

    assert result is True
    assert len(calls) == 1
    assert calls[0][1] == 10


def test_send_json_callback_retries_once_then_returns_false(monkeypatch, caplog):
    calls = []

    def fake_urlopen(req, timeout):
        calls.append((req, timeout))
        raise error.URLError("backend unavailable")

    monkeypatch.setattr(callback_sender.request, "urlopen", fake_urlopen)
    caplog.set_level(logging.WARNING, logger=callback_sender.LOGGER.name)

    result = callback_sender.send_json_callback(
        "http://localhost:8000/api/ai-callback/yolo-result",
        {
            "request_id": "REQ_20260618_001",
            "job_id": "AI_JOB_REQ_20260618_001",
        },
        timeout_seconds=10,
        retry_count=1,
        callback_name="yolo",
    )

    assert result is False
    assert len(calls) == 2
    assert "callback=yolo" in caplog.text
    assert "request_id=REQ_20260618_001" in caplog.text
    assert "job_id=AI_JOB_REQ_20260618_001" in caplog.text
    assert "attempt=1/2" in caplog.text
    assert "attempt=2/2" in caplog.text
    assert "error_type=URLError" in caplog.text
