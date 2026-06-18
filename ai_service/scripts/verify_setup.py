"""Verify imports, model metadata, fixtures, and all deterministic mock scenarios."""

from __future__ import annotations

import json
import shutil
import tempfile
from dataclasses import replace
from pathlib import Path

import _bootstrap
import xgboost as xgb_library
from flood_risk_xgb.config import Settings
from flood_risk_xgb.service import build_default_service


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    root = _bootstrap.ROOT
    local_shadow = (root / "xgboost").resolve()
    imported_from = Path(xgb_library.__file__).resolve()
    if local_shadow in imported_from.parents:
        raise RuntimeError(f"Installed xgboost library was shadowed by the local folder: {imported_from}")

    base_settings = Settings.from_env(root)
    expected_rows = _read_jsonl(root / "mock_data" / "examples" / "expected_outcomes.jsonl")
    expected = {
        int(row["yolo_result_id"]): {
            "risk_level": row["expected_risk_level"],
            "state_code": row["expected_state_code"],
        }
        for row in expected_rows
    }

    with tempfile.TemporaryDirectory(prefix="flood-risk-verify-") as temp_dir:
        temp_mock = Path(temp_dir) / "mock_data"
        shutil.copytree(root / "mock_data" / "fixtures", temp_mock / "fixtures")
        settings = replace(base_settings, mock_data_dir=temp_mock)
        service = build_default_service(settings)
        actual = {
            result.yolo_result_id: {
                "risk_level": str(result.risk_level),
                "state_code": str(result.state_code),
            }
            for result in service.analyze_pending()
        }

    mismatches = {
        result_id: {"expected": expected[result_id], "actual": actual.get(result_id)}
        for result_id in expected
        if actual.get(result_id) != expected[result_id]
    }
    if mismatches:
        raise RuntimeError(f"Mock scenario verification failed: {json.dumps(mismatches, indent=2)}")

    print("Python package: flood_risk_xgb")
    print(f"XGBoost library: {xgb_library.__version__} ({imported_from})")
    print(f"Model: {base_settings.model_path.relative_to(root)}")
    print(f"Verified scenarios: {len(expected)} / {len(expected)}")
    print("Setup verification passed.")


if __name__ == "__main__":
    main()
