"""Regenerate deterministic drain, YOLO, and sensor fixtures."""

from __future__ import annotations

import _bootstrap
from flood_risk_xgb.mock.generator import generate_mock_fixtures


def main() -> None:
    mock_dir = _bootstrap.ROOT / "mock_data"
    generate_mock_fixtures(mock_dir)
    print(f"Generated mock fixtures: {mock_dir}")


if __name__ == "__main__":
    main()
