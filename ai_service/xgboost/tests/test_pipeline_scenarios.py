import json
import shutil
from dataclasses import replace
from pathlib import Path

from flood_risk_xgb.config import Settings
from flood_risk_xgb.service import build_default_service


ROOT = Path(__file__).resolve().parents[1]


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_all_mock_scenarios_match_expected_risk_levels_and_state_codes(tmp_path: Path) -> None:
    mock_dir = tmp_path / "mock_data"
    shutil.copytree(ROOT / "mock_data" / "fixtures", mock_dir / "fixtures")
    settings = replace(Settings.from_env(ROOT), mock_data_dir=mock_dir)
    service = build_default_service(settings)

    actual = {
        result.yolo_result_id: {
            "risk_level": result.risk_level,
            "state_code": result.state_code,
        }
        for result in service.analyze_pending()
    }
    expected = {
        int(row["yolo_result_id"]): {
            "risk_level": row["expected_risk_level"],
            "state_code": row["expected_state_code"],
        }
        for row in _read_jsonl(ROOT / "mock_data" / "examples" / "expected_outcomes.jsonl")
    }

    assert actual == expected


def test_existing_analysis_is_returned_without_duplicate_append(tmp_path: Path) -> None:
    mock_dir = tmp_path / "mock_data"
    shutil.copytree(ROOT / "mock_data" / "fixtures", mock_dir / "fixtures")
    settings = replace(Settings.from_env(ROOT), mock_data_dir=mock_dir)
    service = build_default_service(settings)

    first = service.analyze(1)
    second = service.analyze(1)

    assert first.xgboost_id == second.xgboost_id
    rows = _read_jsonl(mock_dir / "runtime" / "xgboost_data.jsonl")
    assert len(rows) == 1
