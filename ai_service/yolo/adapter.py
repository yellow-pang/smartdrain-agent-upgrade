"""Adapter for the temporary legacy YOLO classification model.

This module intentionally knows the legacy class names. XGBoost must not import it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class NormalizedYoloOutput:
    obstruction_ratio: float
    confidence_score: float
    yolo_status: str
    predicted_class: str


def normalize_classification_output(
    names: Mapping[int, str],
    probabilities: Sequence[float],
) -> NormalizedYoloOutput:
    """Convert legacy class probabilities to the shared YOLO result contract."""
    if not probabilities:
        raise ValueError("YOLO probability vector is empty")

    indexed = [(int(index), float(probability)) for index, probability in enumerate(probabilities)]
    top_index, top_probability = max(indexed, key=lambda item: item[1])
    predicted_class = names[top_index]

    blocked_probability = sum(
        probability
        for index, probability in indexed
        if "blocked" in names[index].lower() or "침수" in names[index]
    )
    obstruction_ratio = min(max(float(blocked_probability), 0.0), 1.0)
    confidence_score = min(max(float(top_probability), 0.0), 1.0)

    if confidence_score < 0.40:
        status = "unknown"
    elif obstruction_ratio >= 0.70:
        status = "danger"
    elif obstruction_ratio >= 0.35:
        status = "caution"
    else:
        status = "good"

    return NormalizedYoloOutput(
        obstruction_ratio=obstruction_ratio,
        confidence_score=confidence_score,
        yolo_status=status,
        predicted_class=predicted_class,
    )
