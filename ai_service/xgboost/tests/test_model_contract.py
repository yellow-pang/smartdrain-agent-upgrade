from pathlib import Path

import xgboost as xgb_library

from flood_risk_xgb.config import Settings
from flood_risk_xgb.features.schema import FEATURE_COLUMNS
from flood_risk_xgb.inference.predictor import RiskPredictor


ROOT = Path(__file__).resolve().parents[2]


def test_installed_xgboost_library_is_not_shadowed_by_project_folder() -> None:
    imported = Path(xgb_library.__file__).resolve()
    assert (ROOT / "xgboost").resolve() not in imported.parents


def test_model_metadata_matches_runtime_feature_order() -> None:
    settings = Settings.from_env(ROOT)
    predictor = RiskPredictor(settings.model_path, settings.model_metadata_path)
    assert predictor.metadata.feature_columns == FEATURE_COLUMNS
    assert predictor.model_version == "xgb-mock-v2.0.0"
