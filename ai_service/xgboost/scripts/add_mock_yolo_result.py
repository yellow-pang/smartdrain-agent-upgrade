"""Append one DB-shaped YOLO mock result to the fixture JSONL file."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import _bootstrap
from flood_risk_xgb.domain import YoloResult


DEFAULT_PATH = _bootstrap.ROOT / "mock_data" / "fixtures" / "yolo_result_data.jsonl"


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drain-id", type=int, required=True)
    parser.add_argument("--obstruction-ratio", type=float, required=True)
    parser.add_argument("--confidence-score", type=float, required=True)
    parser.add_argument(
        "--status",
        required=True,
        help="YOLO status text. Examples: 양호, 더러움, 막힘, 우천원활, 침수, good, caution, danger, unknown.",
    )
    parser.add_argument("--captured-at", help="ISO 8601; defaults to current UTC time")
    parser.add_argument("--image-uri", default="mock://manual-entry/latest.jpg")
    parser.add_argument("--output", type=Path, default=DEFAULT_PATH)
    args = parser.parse_args()

    output = args.output.resolve()
    records = _read(output)
    next_id = max((int(row["yolo_result_id"]) for row in records), default=0) + 1
    candidate = YoloResult(
        yolo_result_id=next_id,
        drain_id=args.drain_id,
        captured_at=args.captured_at or datetime.now(timezone.utc),
        image_uri=args.image_uri,
        obstruction_ratio=args.obstruction_ratio,
        confidence_score=args.confidence_score,
        yolo_status=args.status,
        analysis_target=True,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    payload = candidate.model_dump(mode="json", by_alias=True)
    with output.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
