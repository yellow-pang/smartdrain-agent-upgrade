"""Analyze every YOLO fixture that does not yet have an XGBoost result."""

from __future__ import annotations

import json

import _bootstrap  # noqa: F401
from flood_risk_xgb.service import build_default_service


def main() -> None:
    reports = build_default_service().analyze_pending()
    if not reports:
        print("No pending YOLO results were found.")
        return

    for report in reports:
        print(json.dumps(report.model_dump(mode="json"), ensure_ascii=False))
    print(f"Processed {len(reports)} pending YOLO result(s).")


if __name__ == "__main__":
    main()
