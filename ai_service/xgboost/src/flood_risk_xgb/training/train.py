"""Train and persist the deterministic mock XGBoost baseline."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

from flood_risk_xgb.features.schema import FEATURE_COLUMNS
from flood_risk_xgb.training.generate import generate_training_frame


CLASS_MAPPING = {0: "good", 1: "caution", 2: "danger"}


def train_and_save(output_dir: Path, seed: int = 42) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = generate_training_frame(seed=seed)
    X = frame[FEATURE_COLUMNS]
    y = frame["label"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=seed,
        stratify=y,
    )

    model = xgb.XGBClassifier(
        objective="multi:softprob",
        num_class=3,
        max_depth=5,
        learning_rate=0.06,
        n_estimators=260,
        subsample=0.90,
        colsample_bytree=0.90,
        reg_lambda=1.2,
        random_state=seed,
        n_jobs=4,
        eval_metric="mlogloss",
    )
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    model_path = output_dir / "xgb_mock_baseline.json"
    metadata_path = output_dir / "model_metadata.json"
    evaluation_path = output_dir / "evaluation.json"
    model.save_model(model_path)

    metadata = {
        "model_version": "xgb-mock-v2.0.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mock_only": True,
        "training_data": "deterministic synthetic features",
        "feature_columns": FEATURE_COLUMNS,
        "class_mapping": {str(key): value for key, value in CLASS_MAPPING.items()},
        "risk_score_definition": "probability of the danger class",
        "sensor_lookback_minutes": 30,
        "sensor_short_window_minutes": 5,
        "random_seed": seed,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    report = classification_report(
        y_test,
        predictions,
        labels=[0, 1, 2],
        target_names=[CLASS_MAPPING[index] for index in [0, 1, 2]],
        output_dict=True,
        zero_division=0,
    )
    evaluation = {
        "mock_only": True,
        "training_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "class_distribution": {
            CLASS_MAPPING[index]: int((y == index).sum()) for index in [0, 1, 2]
        },
        "accuracy": float(accuracy_score(y_test, predictions)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, predictions)),
        "confusion_matrix": confusion_matrix(y_test, predictions, labels=[0, 1, 2]).tolist(),
        "classification_report": report,
    }
    evaluation_path.write_text(json.dumps(evaluation, indent=2), encoding="utf-8")
    return evaluation


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    evaluation = train_and_save(root / "models")
    print(json.dumps(evaluation, indent=2))


if __name__ == "__main__":
    main()
