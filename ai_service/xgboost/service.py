from .model_predictor import TrainedXGBoostPredictor


def predict_flood_risk_batch(input_dict_batch: dict) -> list[dict]:
    """Run flood risk inference for the fixed XGBoost batch contract."""
    predictor = TrainedXGBoostPredictor()
    return predictor.predict_batch(input_dict_batch)
