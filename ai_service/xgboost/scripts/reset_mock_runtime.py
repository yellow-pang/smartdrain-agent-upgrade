"""Delete generated XGBoost mock outputs while preserving fixture data."""

from __future__ import annotations

from pathlib import Path

import _bootstrap


ROOT = _bootstrap.ROOT


def main() -> None:
    runtime = ROOT / "mock_data" / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    for filename in ("xgboost_data.jsonl", "analysis_trace.jsonl"):
        path = runtime / filename
        if path.exists():
            path.unlink()
            print(f"Removed: {path.relative_to(ROOT)}")
    (runtime / ".gitkeep").touch()


if __name__ == "__main__":
    main()
