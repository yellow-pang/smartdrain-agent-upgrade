import math
from pathlib import Path

from .constants import FEATURE_COLUMNS, RISK_LEVELS
from .feature_builder import build_feature_rows

AI_SERVICE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_XGBOOST_MODEL_PATH = AI_SERVICE_DIR / "model" / "sewer_xgboost_model.json"
TRAINED_MODEL_VERSION = "sewer_xgboost_model_v1"

RISK_LEVEL_BY_LABEL_INDEX = {
    # 학습 코드의 label encoding과 반드시 같은 순서를 유지해야 한다.
    # 순서가 바뀌면 같은 모델 출력이 다른 위험도로 해석된다.
    0: "good",
    1: "caution",
    2: "danger",
    3: "unknown",
}


class TrainedXGBoostPredictor:
    """Predict flood risk with the trained XGBoost model artifact."""

    def __init__(self, model_path: str | Path | None = None, model=None):
        self.model_path = Path(model_path or DEFAULT_XGBOOST_MODEL_PATH)
        self.model = model if model is not None else self._load_model()

    def predict_batch(self, input_dict_batch: dict) -> list[dict]:
        feature_rows = build_feature_rows(input_dict_batch)
        if not feature_rows:
            return []

        results = []
        for row in feature_rows:
            results.append(self._predict_row(row))
        return results

    def _predict_row(self, row: dict) -> dict:
        feature_snapshot = {column: row[column] for column in FEATURE_COLUMNS}
        if _has_unknown_value(feature_snapshot):
            # 입력 feature 중 하나라도 결측이면 모델 확률을 신뢰할 수 없다.
            # 이 경우 강제로 unknown을 반환해 후속 현장 확인 흐름으로 넘긴다.
            return _build_unknown_result(row["index"], feature_snapshot)

        feature_matrix = [[feature_snapshot[column] for column in FEATURE_COLUMNS]]
        prediction = self.model.predict(feature_matrix)
        probabilities = self.model.predict_proba(feature_matrix)

        label_index = int(prediction[0])
        risk_level = _risk_level_from_label_index(label_index)
        risk_score = _risk_score_from_probabilities(probabilities[0], label_index)

        return {
            "index": row["index"],
            "risk_level": risk_level,
            "risk_score": risk_score,
            "final_decision": risk_level,
            "feature_snapshot": feature_snapshot,
            "model_version": TRAINED_MODEL_VERSION,
        }

    def _load_model(self):
        import xgboost as xgb

        model = xgb.XGBClassifier()
        model.load_model(str(self.model_path))
        return model


def predict_flood_risk_batch_with_trained_model(input_dict_batch: dict) -> list[dict]:
    return TrainedXGBoostPredictor().predict_batch(input_dict_batch)


def _risk_level_from_label_index(label_index: int) -> str:
    try:
        return RISK_LEVEL_BY_LABEL_INDEX[label_index]
    except KeyError as exc:
        raise ValueError(f"Unsupported XGBoost label index: {label_index}") from exc


def _risk_score_from_probabilities(probabilities, label_index: int) -> float:
    return round(float(probabilities[label_index]), 4)


def _has_unknown_value(feature_snapshot: dict) -> bool:
    return any(_is_none_or_nan(value) for value in feature_snapshot.values())


def _is_none_or_nan(value: object) -> bool:
    if value is None:
        return True
    try:
        return math.isnan(value)
    except TypeError:
        return False


def _build_unknown_result(index: int, feature_snapshot: dict) -> dict:
    return {
        "index": index,
        "risk_level": "unknown",
        "risk_score": 0.0,
        "final_decision": "unknown",
        "feature_snapshot": feature_snapshot,
        "model_version": TRAINED_MODEL_VERSION,
    }


def validate_label_mapping_covers_risk_levels() -> None:
    mapped_levels = tuple(RISK_LEVEL_BY_LABEL_INDEX[index] for index in sorted(RISK_LEVEL_BY_LABEL_INDEX))
    if mapped_levels != RISK_LEVELS:
        raise ValueError("XGBoost label mapping does not match RISK_LEVELS.")
