"""Analyze one YOLO result ID and persist an XGBoost result."""

from __future__ import annotations

import argparse
import json

import _bootstrap  # noqa: F401
from flood_risk_xgb.service import build_default_service


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yolo-result-id", type=int, required=True)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Append a new analysis even if the YOLO result was processed before.",
    )
    args = parser.parse_args()

    report = build_default_service().analyze(args.yolo_result_id, force=args.force)
    print(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
