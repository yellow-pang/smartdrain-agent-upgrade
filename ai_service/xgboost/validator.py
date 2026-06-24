from .constants import FEATURE_COLUMNS


def validate_input_batch(input_dict_batch: dict) -> None:
    """Validate the fixed dict-of-list XGBoost inference batch contract."""
    if not isinstance(input_dict_batch, dict):
        raise ValueError("input_dict_batch must be a dict.")

    missing_keys = [key for key in FEATURE_COLUMNS if key not in input_dict_batch]
    if missing_keys:
        raise ValueError(f"Missing required feature keys: {missing_keys}")

    lengths = []
    for key in FEATURE_COLUMNS:
        values = input_dict_batch[key]
        if not isinstance(values, list):
            raise ValueError(f"Feature '{key}' must be a list.")
        lengths.append(len(values))

    if len(set(lengths)) != 1:
        raise ValueError("All feature lists must have the same length.")
