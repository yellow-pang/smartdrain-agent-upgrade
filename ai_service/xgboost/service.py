from .feature_builder import build_feature_rows
from .rule_baseline_predictor import RuleBaselinePredictor


def predict_flood_risk_batch(input_dict_batch: dict) -> list[dict]:
    """Run flood risk inference for the fixed XGBoost batch contract."""
    feature_rows = build_feature_rows(input_dict_batch)
    predictor = RuleBaselinePredictor()
    return predictor.predict(feature_rows)
