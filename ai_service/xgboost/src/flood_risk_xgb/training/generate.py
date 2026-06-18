"""Generate deterministic synthetic feature rows for the development baseline."""

from __future__ import annotations

import numpy as np
import pandas as pd

from flood_risk_xgb.features.schema import FEATURE_COLUMNS


CLASS_TO_ID = {"good": 0, "caution": 1, "danger": 2}


def heuristic_label(row: pd.Series) -> int:
    obstruction = float(row["obstruction_ratio"])
    confidence = float(row["confidence_score"])
    obstruction_delta = float(row["obstruction_delta_30m"])
    obstruction_persistence = float(row["obstruction_persistence_count_30m"])
    water = float(row["water_level_latest"])
    flow = float(row["flow_velocity_latest"])
    water_delta_5m = float(row["water_level_delta_5m"])
    water_delta_30m = float(row["water_level_delta_30m"])
    water_slope = float(row["water_level_slope_30m"])
    flow_delta_30m = float(row["flow_velocity_delta_30m"])
    effective_obstruction = obstruction * (0.35 + 0.65 * confidence)

    clear_sensor_danger = (
        water >= 85.0
        and flow <= 0.25
        and (water_delta_5m >= 7.0 or water_delta_30m >= 15.0 or flow <= 0.12)
    ) or (
        water >= 70.0 and flow <= 0.12 and water_delta_30m >= 8.0
    ) or (
        water >= 70.0 and flow <= 0.25 and water_delta_30m >= 18.0
    )
    combined_danger = water >= 65.0 and effective_obstruction >= 0.50 and flow <= 0.28
    progressive_danger = (
        obstruction_delta >= 0.18
        and obstruction_persistence >= 2
        and water_slope >= 0.45
        and flow_delta_30m <= -0.15
    )

    if clear_sensor_danger or combined_danger or progressive_danger:
        return CLASS_TO_ID["danger"]

    dry_visual_blockage = water < 25.0 and obstruction >= 0.70 and confidence >= 0.40
    hydraulic_caution = water >= 65.0 and flow >= 0.55 and water_delta_30m >= 8.0
    caution_signal = (
        dry_visual_blockage
        or hydraulic_caution
        or water >= 75.0
        or water_delta_30m >= 12.0
        or (water >= 45.0 and (water_delta_30m >= 5.0 or flow <= 0.35))
        or (effective_obstruction >= 0.35 and water >= 20.0)
    )
    if caution_signal:
        return CLASS_TO_ID["caution"]

    return CLASS_TO_ID["good"]


def _base_frame(n_samples: int, rng: np.random.Generator) -> pd.DataFrame:
    obstruction = rng.beta(1.6, 2.2, n_samples)
    confidence = rng.beta(5.0, 1.5, n_samples)
    obstruction_delta_30m = rng.normal(0.02, 0.18, n_samples)
    obstruction_mean_30m = np.clip(obstruction - obstruction_delta_30m / 2 + rng.normal(0, 0.03, n_samples), 0, 1)
    obstruction_persistence = np.where(obstruction_mean_30m >= 0.65, rng.integers(2, 5, n_samples), rng.integers(0, 2, n_samples)).astype(float)

    water_start = rng.uniform(0.0, 70.0, n_samples)
    water_delta_30m = rng.normal(6.0, 16.0, n_samples)
    water_latest = np.clip(water_start + water_delta_30m, 0.0, 110.0)
    water_delta_30m = water_latest - water_start
    water_delta_5m = water_delta_30m * rng.uniform(0.10, 0.28, n_samples) + rng.normal(
        0.0, 1.8, n_samples
    )

    flow_start = rng.uniform(0.0, 1.4, n_samples)
    flow_delta_30m = -0.010 * water_delta_30m + rng.normal(0.0, 0.18, n_samples)
    flow_latest = np.clip(flow_start + flow_delta_30m, 0.0, 2.0)
    flow_delta_30m = flow_latest - flow_start
    flow_delta_5m = flow_delta_30m * rng.uniform(0.10, 0.28, n_samples) + rng.normal(
        0.0, 0.03, n_samples
    )

    water_mean_30m = np.clip((water_start + water_latest) / 2 + rng.normal(0, 1.5, n_samples), 0, None)
    flow_mean_30m = np.clip((flow_start + flow_latest) / 2 + rng.normal(0, 0.04, n_samples), 0, None)
    water_mean_5m = np.clip(water_latest - water_delta_5m / 2 + rng.normal(0, 0.5, n_samples), 0, None)
    flow_mean_5m = np.clip(flow_latest - flow_delta_5m / 2 + rng.normal(0, 0.015, n_samples), 0, None)

    frame = pd.DataFrame(
        {
            "obstruction_ratio": obstruction,
            "confidence_score": confidence,
            "obstruction_mean_30m": obstruction_mean_30m,
            "obstruction_delta_30m": obstruction_delta_30m,
            "obstruction_persistence_count_30m": obstruction_persistence,
            "water_level_latest": water_latest,
            "flow_velocity_latest": flow_latest,
            "water_level_mean_5m": water_mean_5m,
            "flow_velocity_mean_5m": flow_mean_5m,
            "water_level_delta_5m": water_delta_5m,
            "flow_velocity_delta_5m": flow_delta_5m,
            "water_level_mean_30m": water_mean_30m,
            "flow_velocity_mean_30m": flow_mean_30m,
            "water_level_delta_30m": water_delta_30m,
            "flow_velocity_delta_30m": flow_delta_30m,
            "water_level_slope_30m": water_delta_30m / 30.0,
            "flow_velocity_slope_30m": flow_delta_30m / 30.0,
            "water_level_max_30m": np.maximum(water_start, water_latest)
            + np.abs(rng.normal(0, 1.0, n_samples)),
            "flow_velocity_min_30m": np.clip(
                np.minimum(flow_start, flow_latest) - np.abs(rng.normal(0, 0.02, n_samples)),
                0,
                None,
            ),
            "water_level_std_30m": np.abs(water_delta_30m) / 3.8 + rng.uniform(0, 1.2, n_samples),
            "flow_velocity_std_30m": np.abs(flow_delta_30m) / 3.8 + rng.uniform(0, 0.04, n_samples),
            "sensor_age_seconds": rng.uniform(0, 180, n_samples),
            "sensor_count_30m": rng.integers(20, 32, n_samples).astype(float),
            "sensor_valid_ratio_30m": rng.uniform(0.75, 1.0, n_samples),
        }
    )
    return frame[FEATURE_COLUMNS]


def _stress_prototypes() -> list[tuple[dict[str, float], int]]:
    def row(
        obstruction: float,
        confidence: float,
        obstruction_delta: float,
        water: float,
        flow: float,
        water_delta: float,
        flow_delta: float,
        label: str,
    ) -> tuple[dict[str, float], int]:
        water_delta_5 = water_delta / 6.0
        flow_delta_5 = flow_delta / 6.0
        payload = {
            "obstruction_ratio": obstruction,
            "confidence_score": confidence,
            "obstruction_mean_30m": float(np.clip(obstruction - obstruction_delta / 2, 0, 1)),
            "obstruction_delta_30m": obstruction_delta,
            "obstruction_persistence_count_30m": 4.0 if obstruction >= 0.65 else 1.0,
            "water_level_latest": water,
            "flow_velocity_latest": flow,
            "water_level_mean_5m": max(0.0, water - water_delta_5 / 2),
            "flow_velocity_mean_5m": max(0.0, flow - flow_delta_5 / 2),
            "water_level_delta_5m": water_delta_5,
            "flow_velocity_delta_5m": flow_delta_5,
            "water_level_mean_30m": max(0.0, water - water_delta / 2),
            "flow_velocity_mean_30m": max(0.0, flow - flow_delta / 2),
            "water_level_delta_30m": water_delta,
            "flow_velocity_delta_30m": flow_delta,
            "water_level_slope_30m": water_delta / 30.0,
            "flow_velocity_slope_30m": flow_delta / 30.0,
            "water_level_max_30m": max(water, water - water_delta),
            "flow_velocity_min_30m": max(0.0, min(flow, flow - flow_delta)),
            "water_level_std_30m": abs(water_delta) / 3.8,
            "flow_velocity_std_30m": abs(flow_delta) / 3.8,
            "sensor_age_seconds": 30.0,
            "sensor_count_30m": 31.0,
            "sensor_valid_ratio_30m": 1.0,
        }
        return payload, CLASS_TO_ID[label]

    return [
        row(0.10, 0.10, 0.00, 95, 0.00, 45, -0.30, "danger"),
        row(0.05, 0.95, 0.00, 88, 0.80, 1, 0.00, "caution"),
        row(0.65, 0.90, 0.05, 40, 0.20, 15, -0.35, "caution"),
        row(0.88, 0.92, 0.20, 85, 0.05, 50, -0.50, "danger"),
        row(0.85, 0.90, 0.00, 10, 0.50, 0, 0.00, "good"),
        row(0.20, 0.90, 0.00, 100, 0.00, 45, -0.20, "danger"),
        row(0.98, 0.98, 0.00, 5, 0.00, 0, 0.00, "caution"),
        row(0.90, 0.90, 0.00, 0, 0.00, 0, 0.00, "caution"),
        row(0.15, 0.90, 0.00, 75, 0.05, 35, -0.20, "danger"),
        row(0.05, 0.95, 0.00, 10, 0.00, 0, 0.00, "good"),
        row(0.25, 0.90, 0.00, 80, 0.75, 30, 0.10, "caution"),
        row(0.84, 0.91, 0.42, 78, 0.18, 42, -0.45, "danger"),
    ]


def generate_training_frame(n_samples: int = 24000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    frame = _base_frame(n_samples, rng)
    frame["label"] = frame.apply(heuristic_label, axis=1)

    augmented_rows: list[dict[str, float]] = []
    augmented_labels: list[int] = []
    for prototype, label in _stress_prototypes():
        for _ in range(220):
            noisy = prototype.copy()
            for key in FEATURE_COLUMNS:
                scale = 0.01 if key in {"obstruction_ratio", "confidence_score"} else 0.02
                if key in {"sensor_count_30m", "sensor_valid_ratio_30m", "obstruction_persistence_count_30m"}:
                    continue
                magnitude = max(abs(noisy[key]), 1.0)
                noisy[key] += float(rng.normal(0.0, scale * magnitude))
            noisy["obstruction_ratio"] = float(np.clip(noisy["obstruction_ratio"], 0, 1))
            noisy["confidence_score"] = float(np.clip(noisy["confidence_score"], 0, 1))
            noisy["obstruction_mean_30m"] = float(np.clip(noisy["obstruction_mean_30m"], 0, 1))
            noisy["sensor_valid_ratio_30m"] = float(np.clip(noisy["sensor_valid_ratio_30m"], 0, 1))
            for key in [
                "water_level_latest",
                "flow_velocity_latest",
                "water_level_mean_5m",
                "flow_velocity_mean_5m",
                "water_level_mean_30m",
                "flow_velocity_mean_30m",
                "water_level_max_30m",
                "flow_velocity_min_30m",
                "water_level_std_30m",
                "flow_velocity_std_30m",
                "sensor_age_seconds",
            ]:
                noisy[key] = max(0.0, noisy[key])
            augmented_rows.append(noisy)
            augmented_labels.append(label)

    augmented = pd.DataFrame(augmented_rows, columns=FEATURE_COLUMNS)
    augmented["label"] = augmented_labels
    combined = pd.concat([frame, augmented], ignore_index=True)

    # Small label noise prevents the mock model from appearing unrealistically perfect.
    noise_mask = rng.random(len(combined)) < 0.012
    noisy_indices = np.flatnonzero(noise_mask)
    for index in noisy_indices:
        current = int(combined.at[index, "label"])
        combined.at[index, "label"] = int(rng.choice([value for value in (0, 1, 2) if value != current]))

    return combined
