import math

from .constants import FEATURE_COLUMNS, MODEL_VERSION, YOLO_CONFIDENCE_THRESHOLD


class RuleBaselinePredictor:
    """Temporary rule-based predictor until a trained XGBoost model is available."""

    def predict(self, feature_rows: list[dict]) -> list[dict]:
        return [self._predict_row(row) for row in feature_rows]

    def _predict_row(self, row: dict) -> dict:
        feature_snapshot = {column: row[column] for column in FEATURE_COLUMNS}

        if self._has_unknown_value(feature_snapshot):
            risk_level = "unknown"
            risk_score = 0.0
        else:
            risk_level, risk_score = self._apply_rules(feature_snapshot)

        return {
            "index": row["index"],
            "risk_level": risk_level,
            "risk_score": risk_score,
            "final_decision": risk_level,
            "feature_snapshot": feature_snapshot,
            "model_version": MODEL_VERSION,
        }

    def _has_unknown_value(self, feature_snapshot: dict) -> bool:
        return any(self._is_none_or_nan(value) for value in feature_snapshot.values())

    def _is_none_or_nan(self, value: object) -> bool:
        if value is None:
            return True
        try:
            return math.isnan(value)
        except TypeError:
            return False

    def _apply_rules(self, feature_snapshot: dict) -> tuple[str, float]:
        obstruction_ratio = feature_snapshot["obstruction_ratio"]
        confidence_score = feature_snapshot["confidence_score"]
        water_level = feature_snapshot["water_level"]
        flow_velocity = feature_snapshot["flow_velocity"]

        if confidence_score < YOLO_CONFIDENCE_THRESHOLD:
            return "unknown", 0.0

        if water_level >= 0.70 and flow_velocity <= 0.30:
            return "danger", 0.85

        if obstruction_ratio >= 0.75 and water_level >= 0.50:
            return "danger", 0.80

        if water_level >= 0.35 or obstruction_ratio >= 0.30:
            return "caution", 0.65

        return "good", 0.90
