"""Run the temporary YOLO PoC and append a DB-shaped JSONL record."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from inference import run_inference


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = Path(__file__).resolve().parent / "models" / "best.pt"
DEFAULT_OUTPUT = ROOT / "mock_data" / "fixtures" / "yolo_result_data.jsonl"


def _read_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            records.append(json.loads(line))
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--drain-id", type=int, required=True)
    parser.add_argument("--captured-at", help="ISO 8601 timestamp; defaults to current UTC time")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    normalized = run_inference(args.image, args.model)
    output_path = args.output.resolve()
    existing = _read_records(output_path)
    next_id = max((int(row["yolo_result_id"]) for row in existing), default=0) + 1

    captured_at = args.captured_at or datetime.now(timezone.utc).isoformat()
    record = {
        "yolo_result_id": next_id,
        "drain_id": args.drain_id,
        "captured_at": captured_at,
        "image_uri": str(args.image.resolve()),
        "obstruction_ratio": round(normalized.obstruction_ratio, 4),
        "confidence_score": round(normalized.confidence_score, 4),
        "yolo_status": normalized.yolo_status,
        "analysis_target": True,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(json.dumps({**record, "legacy_predicted_class": normalized.predicted_class}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
