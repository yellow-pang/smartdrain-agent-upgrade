"""Lazy inference wrapper for the temporary legacy YOLO model."""

from __future__ import annotations

from pathlib import Path

from adapter import NormalizedYoloOutput, normalize_classification_output


def run_inference(image_path: Path, model_path: Path) -> NormalizedYoloOutput:
    try:
        from ultralytics import YOLO
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "ultralytics is not installed. Install requirements/yolo-poc.txt first."
        ) from exc

    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")
    if not model_path.is_file():
        raise FileNotFoundError(f"YOLO model not found: {model_path}")

    model = YOLO(str(model_path))
    results = model(str(image_path), verbose=False)
    result = results[0]

    if result.probs is None:
        raise RuntimeError(
            "The temporary adapter expects an Ultralytics classification result with probabilities."
        )

    probabilities = result.probs.data.detach().cpu().tolist()
    return normalize_classification_output(result.names, probabilities)
