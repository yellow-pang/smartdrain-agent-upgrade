"""Retrain the synthetic XGBoost baseline and update metadata/evaluation files."""

from __future__ import annotations

import json

import _bootstrap
from flood_risk_xgb.training.train import train_and_save


def main() -> None:
    evaluation = train_and_save(_bootstrap.ROOT / "xgboost" / "models")
    print(json.dumps(evaluation, ensure_ascii=False, indent=2))
    print("This is a synthetic development baseline, not operational performance evidence.")


if __name__ == "__main__":
    main()
