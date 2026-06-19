from .constants import FEATURE_COLUMNS
from .validator import validate_input_batch


def build_feature_rows(input_dict_batch: dict) -> list[dict]:
    """Convert a dict-of-list batch into row-level feature dictionaries."""
    validate_input_batch(input_dict_batch)

    row_count = len(input_dict_batch[FEATURE_COLUMNS[0]])
    rows = []
    for index in range(row_count):
        row = {"index": index}
        for column in FEATURE_COLUMNS:
            row[column] = input_dict_batch[column][index]
        rows.append(row)

    return rows
