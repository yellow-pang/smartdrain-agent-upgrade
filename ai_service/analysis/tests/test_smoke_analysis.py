import hashlib
import sys
from copy import deepcopy
from types import SimpleNamespace

import pytest

from ai_service.scripts import smoke_analysis


@pytest.fixture
def reference_smoke(monkeypatch, tmp_path):
    paths = {}
    arguments = ["smoke_analysis", "--drain-id", "2", "--verify-reference"]
    for name in ("yolo", "sample", "xgboost"):
        path = tmp_path / name
        path.write_bytes(f"approved {name}".encode())
        paths[name] = path
        arguments.extend([f"--expected-{name}-sha256", hashlib.sha256(path.read_bytes()).hexdigest()])
    arguments.extend([
        "--expected-yolo-status", "good",
        "--expected-risk-level", "unknown",
        "--expected-final-decision", "field_check",
    ])
    monkeypatch.setattr(sys, "argv", arguments)
    monkeypatch.setattr(smoke_analysis, "DEFAULT_YOLO_MODEL_PATH", paths["yolo"])
    monkeypatch.setattr(smoke_analysis, "DEFAULT_XGBOOST_MODEL_PATH", paths["xgboost"])
    monkeypatch.setattr(
        smoke_analysis, "resolve_image_source_by_drain_id",
        lambda drain_id: SimpleNamespace(drain_id=drain_id, source_url="mock://sample", local_path=str(paths["sample"])),
    )
    result = {
        "accepted_response": {
            "request_id": "REQ_SMOKE_LOCAL", "job_id": "AI_JOB_REQ_SMOKE_LOCAL",
            "accepted": True, "status": "processing",
        },
        "yolo_callback_payload": {
            "request_id": "REQ_SMOKE_LOCAL", "job_id": "AI_JOB_REQ_SMOKE_LOCAL",
            "yolo_result": {"obstruction_ratio": 0.22, "confidence_score": 0.98, "yolo_status": "good"},
        },
        "xgboost_callback_payload": {
            "request_id": "REQ_SMOKE_LOCAL", "job_id": "AI_JOB_REQ_SMOKE_LOCAL",
            "xgboost_result": {
                "risk_score": 0.85, "risk_level": "unknown", "final_decision": "field_check",
                "evaluated_at": "2026-06-18T09:00:00+09:00",
            },
        },
    }
    calls = []

    def analyze(payload):
        calls.append(deepcopy(payload))
        return result

    monkeypatch.setattr(smoke_analysis, "run_analysis_job", analyze)
    return SimpleNamespace(paths=paths, arguments=arguments, result=result, calls=calls)


def test_reference_smoke_accepts_normal_xgboost_unknown_and_runs_inference_once(reference_smoke, capsys):
    assert smoke_analysis.main() == 0
    assert "[PASS]" in capsys.readouterr().out
    assert len(reference_smoke.calls) == 1
    assert reference_smoke.calls[0]["drain_id"] == 2
    assert reference_smoke.calls[0]["sensor_data"] == {
        "measured_at": "2026-06-18T08:36:13+09:00",
        "water_level_cm": 98.13, "flow_velocity_mps": 0.4512, "quality_status": "valid",
    }


@pytest.mark.parametrize(("path", "value"), [
    (("yolo_callback_payload", "yolo_result"), {"obstruction_ratio": -1.0, "confidence_score": -1.0, "yolo_status": "unknown"}),
    (("yolo_callback_payload", "job_id"), "wrong-job"),
    (("accepted_response", "status"), "completed"),
    (("xgboost_callback_payload", "xgboost_result", "risk_score"), float("nan")),
    (("xgboost_callback_payload", "xgboost_result", "risk_level"), "danger"),
    (("xgboost_callback_payload", "xgboost_result", "final_decision"), "normal"),
    (("xgboost_callback_payload", "xgboost_result", "evaluated_at"), "2026-06-18T09:00:00"),
    (("xgboost_callback_payload", "xgboost_result"), None),
])
def test_reference_smoke_rejects_false_success(reference_smoke, capsys, path, value):
    target = reference_smoke.result
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value

    assert smoke_analysis.main() == 1
    output = capsys.readouterr().out
    assert "[ERROR]" in output
    assert "[PASS]" not in output
    assert len(reference_smoke.calls) == 1


@pytest.mark.parametrize("artifact_name", ["yolo", "sample", "xgboost"])
def test_reference_smoke_stops_before_inference_for_changed_artifact(reference_smoke, artifact_name):
    reference_smoke.paths[artifact_name].write_bytes(b"unapproved replacement")

    assert smoke_analysis.main() == 1
    assert reference_smoke.calls == []


@pytest.mark.parametrize("change", ["missing-expectations", "different-input"])
def test_reference_smoke_requires_explicit_baseline_and_fixed_inputs(reference_smoke, monkeypatch, change):
    if change == "missing-expectations":
        monkeypatch.setattr(sys, "argv", ["smoke_analysis", "--drain-id", "2", "--verify-reference"])
    else:
        reference_smoke.arguments.extend(["--water-level-cm", "1"])

    with pytest.raises(SystemExit) as exc:
        smoke_analysis.main()
    assert exc.value.code == 2
    assert reference_smoke.calls == []


def test_reference_smoke_returns_failure_when_inference_raises(reference_smoke, monkeypatch):
    def failing_analysis(payload):
        raise RuntimeError("model inference failed")

    monkeypatch.setattr(smoke_analysis, "run_analysis_job", failing_analysis)
    assert smoke_analysis.main() == 1


def test_general_smoke_still_works_without_reference_arguments(reference_smoke, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["smoke_analysis", "--drain-id", "2"])
    assert smoke_analysis.main() == 0
    assert len(reference_smoke.calls) == 1
