"""Load an XGBoost model and enforce its feature contract."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import xgboost as xgb

from flood_risk_xgb.domain import RiskLevel
from flood_risk_xgb.exceptions import ModelContractError
from flood_risk_xgb.features.schema import FEATURE_COLUMNS, FeatureVector


@dataclass(frozen=True)
class Prediction:
    risk_level: RiskLevel
    risk_score: float
    class_probabilities: dict[str, float]


@dataclass(frozen=True)
class ModelMetadata:
    model_version: str
    feature_columns: list[str]
    class_mapping: dict[int, RiskLevel]
    risk_score_definition: str

    @classmethod
    def load(cls, path: Path) -> "ModelMetadata":
        payload = json.loads(path.read_text(encoding="utf-8"))
        mapping = {
            int(class_id): RiskLevel(level)
            for class_id, level in payload["class_mapping"].items()
        }
        return cls(
            model_version=str(payload["model_version"]),
            feature_columns=list(payload["feature_columns"]),
            class_mapping=mapping,
            risk_score_definition=str(payload["risk_score_definition"]),
        )


class RiskPredictor:
    def __init__(self, model_path: Path, metadata_path: Path) -> None:
        if not model_path.is_file():
            raise FileNotFoundError(f"XGBoost model not found: {model_path}")
        if not metadata_path.is_file():
            raise FileNotFoundError(f"Model metadata not found: {metadata_path}")

        self.metadata = ModelMetadata.load(metadata_path)
        if self.metadata.feature_columns != FEATURE_COLUMNS:
            raise ModelContractError(
                "Runtime FEATURE_COLUMNS do not match model metadata. "
                "Retrain the model or restore the matching feature code."
            )

        self.model = xgb.XGBClassifier()
        self.model.load_model(model_path)

    @property
    def model_version(self) -> str:
        return self.metadata.model_version

    def predict(self, features: FeatureVector) -> Prediction:
        ordered = features.as_ordered_dict()
        runtime_columns = list(ordered)
        if runtime_columns != self.metadata.feature_columns:
            raise ModelContractError(
                f"Feature order mismatch: {runtime_columns} != {self.metadata.feature_columns}"
            )

        frame = pd.DataFrame([ordered], columns=self.metadata.feature_columns)
        probabilities = self.model.predict_proba(frame)[0]
        if len(probabilities) != len(self.metadata.class_mapping):
            raise ModelContractError(
                "Model probability count does not match metadata class mapping"
            )

        probability_by_level = {
            self.metadata.class_mapping[index].value: float(probability)
            for index, probability in enumerate(probabilities)
        }
        predicted_index = int(probabilities.argmax())
        risk_level = self.metadata.class_mapping[predicted_index]
        danger_probability = probability_by_level[RiskLevel.DANGER.value]

        return Prediction(
            risk_level=risk_level,
            risk_score=danger_probability,
            class_probabilities=probability_by_level,
        )
