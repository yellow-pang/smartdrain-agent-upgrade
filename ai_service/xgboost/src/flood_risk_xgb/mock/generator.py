"""Generate deterministic DB-shaped mock fixtures for integration development."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable


REFERENCE_TIME = datetime.fromisoformat("2026-06-18T14:30:00+09:00")


@dataclass(frozen=True)
class Scenario:
    yolo_result_id: int
    drain_id: int
    drain_code: str
    address: str
    obstruction_ratio: float
    confidence_score: float
    yolo_status: str
    water_start: float
    water_end: float
    flow_start: float
    flow_end: float
    expected_risk_level: str
    expected_state_code: str
    sensor_mode: str = "normal"
    obstruction_history: tuple[float, float, float] | None = None


SCENARIOS = [
    Scenario(1, 101, "DR-101", "정상 배수", 0.08, 0.96, "양호", 10, 12, 0.82, 0.78, "good", "NORMAL_DRAINAGE"),
    Scenario(2, 102, "DR-102", "상부만 막힘·배수 정상", 0.82, 0.91, "막힘", 13, 15, 0.82, 0.76, "caution", "SURFACE_OBSTRUCTION_LIKELY", obstruction_history=(0.72, 0.78, 0.80)),
    Scenario(3, 103, "DR-103", "건조 상태 상부 이물질", 0.92, 0.93, "막힘", 5, 6, 0.02, 0.02, "caution", "DRY_SURFACE_OBSTRUCTION", obstruction_history=(0.88, 0.90, 0.92)),
    Scenario(4, 104, "DR-104", "상부·내부 복합 막힘", 0.88, 0.94, "침수", 35, 72, 0.55, 0.18, "danger", "COMBINED_OBSTRUCTION", obstruction_history=(0.70, 0.78, 0.84)),
    Scenario(5, 105, "DR-105", "심각한 완전 막힘", 0.95, 0.97, "침수", 60, 98, 0.25, 0.00, "danger", "SEVERE_OBSTRUCTION", obstruction_history=(0.85, 0.92, 0.95)),
    Scenario(6, 106, "DR-106", "YOLO 정상이나 내부·하류 막힘", 0.15, 0.92, "양호", 40, 82, 0.35, 0.04, "danger", "INTERNAL_OR_DOWNSTREAM_OBSTRUCTION_SUSPECTED"),
    Scenario(7, 107, "DR-107", "과도한 유입", 0.12, 0.95, "우천원활", 35, 82, 0.50, 0.86, "caution", "HYDRAULIC_OVERLOAD"),
    Scenario(8, 108, "DR-108", "과도한 유입 + 상부 막힘", 0.74, 0.91, "막힘", 30, 74, 0.42, 0.78, "caution", "HIGH_INFLOW_WITH_SURFACE_OBSTRUCTION", obstruction_history=(0.55, 0.68, 0.72)),
    Scenario(9, 109, "DR-109", "용량 근접 안정 상태", 0.10, 0.94, "우천원활", 76, 78, 0.70, 0.72, "caution", "NEAR_CAPACITY_STABLE"),
    Scenario(10, 110, "DR-110", "위험 상태 회복 중", 0.32, 0.91, "더러움", 88, 60, 0.18, 0.55, "good", "RECOVERING", obstruction_history=(0.60, 0.45, 0.36)),
    Scenario(11, 111, "DR-111", "진행성 막힘", 0.86, 0.93, "막힘", 25, 78, 0.72, 0.18, "danger", "PROGRESSIVE_OBSTRUCTION", obstruction_history=(0.22, 0.48, 0.66)),
    Scenario(12, 112, "DR-112", "간헐적 막힘", 0.63, 0.88, "막힘", 30, 58, 0.62, 0.28, "caution", "INTERMITTENT_OBSTRUCTION", "normal", (0.25, 0.78, 0.40)),
    Scenario(13, 113, "DR-113", "YOLO 오탐 의심", 0.88, 0.10, "막힘", 11, 12, 0.80, 0.80, "unknown", "LOW_CONFIDENCE_VISION", obstruction_history=(0.05, 0.12, 0.09)),
    Scenario(14, 114, "DR-114", "수위 센서 순간 Spike", 0.05, 0.95, "양호", 10, 10, 0.80, 0.80, "caution", "WATER_LEVEL_SPIKE", "latest_spike"),
    Scenario(15, 115, "DR-115", "유속 센서 고정", 0.18, 0.94, "양호", 18, 42, 0.40, 0.40, "good", "FLOW_SENSOR_STUCK", "flow_stuck"),
    Scenario(16, 116, "DR-116", "센서 데이터 지연", 0.20, 0.85, "양호", 20, 20, 0.50, 0.50, "unknown", "STALE_SENSOR_DATA", "stale"),
    Scenario(17, 117, "DR-117", "유효 센서 데이터 없음", 0.30, 0.08, "판단불가", 30, 35, 0.40, 0.30, "unknown", "NO_VALID_SENSOR_DATA", "invalid_only"),
    Scenario(18, 118, "DR-118", "YOLO 정상·센서 숨은 위험", 0.08, 0.96, "양호", 52, 92, 0.20, 0.02, "danger", "SENSOR_DETECTED_HIDDEN_RISK"),
]


def _jsonl_write(path: Path, records: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records)
    path.write_text(payload, encoding="utf-8")


def _sensor_series(scenario: Scenario) -> list[dict]:
    records: list[dict] = []

    if scenario.sensor_mode == "stale":
        start = REFERENCE_TIME - timedelta(minutes=36)
        points = 31
    else:
        start = REFERENCE_TIME - timedelta(minutes=60)
        points = 61

    for index in range(points):
        ratio = index / max(points - 1, 1)
        measured_at = start + timedelta(minutes=index)
        water = scenario.water_start + (scenario.water_end - scenario.water_start) * ratio
        flow = scenario.flow_start + (scenario.flow_end - scenario.flow_start) * ratio

        # Small deterministic variation keeps the histories realistic without randomness.
        water += math.sin(index / 4.0) * 0.20
        flow += math.sin(index / 5.0) * 0.005
        quality = "valid"

        if scenario.sensor_mode == "latest_spike" and index == points - 1:
            water = 88.0
        if scenario.sensor_mode == "invalid_only":
            quality = "suspect" if index % 2 == 0 else "missing"
        if scenario.sensor_mode == "flow_stuck":
            flow = 0.400
        if scenario.sensor_mode == "oscillating":
            water = 44.0 + (18.0 if index % 2 == 0 else -10.0) + ratio * 10.0
            flow = max(0.05, 0.62 - ratio * 0.35)

        records.append(
            {
                "measured_at": measured_at.isoformat(),
                "drain_id": scenario.drain_id,
                "water_level_cm": round(max(water, 0.0), 2),
                "flow_velocity_mps": round(max(flow, 0.0), 3),
                "quality_status": quality,
            }
        )
    return records


def _yolo_records(scenario: Scenario) -> list[dict]:
    history = scenario.obstruction_history or (
        max(0.0, scenario.obstruction_ratio - 0.04),
        max(0.0, scenario.obstruction_ratio - 0.02),
        scenario.obstruction_ratio,
    )
    records: list[dict] = []
    for offset, obstruction in zip([-30, -20, -10], history, strict=False):
        captured_at = REFERENCE_TIME + timedelta(minutes=offset)
        records.append(
            {
                "yolo_result_id": 10000 + scenario.yolo_result_id * 10 + abs(offset),
                "drain_id": scenario.drain_id,
                "captured_at": captured_at.isoformat(),
                "image_uri": f"mock://{scenario.drain_code.lower()}/history_{abs(offset)}m.jpg",
                "obstruction_ratio": round(float(obstruction), 4),
                "confidence_score": scenario.confidence_score,
                "yolo_status": scenario.yolo_status,
                "analysis_target": False,
            }
        )
    records.append(
        {
            "yolo_result_id": scenario.yolo_result_id,
            "drain_id": scenario.drain_id,
            "captured_at": REFERENCE_TIME.isoformat(),
            "image_uri": f"mock://{scenario.drain_code.lower()}/latest.jpg",
            "obstruction_ratio": scenario.obstruction_ratio,
            "confidence_score": scenario.confidence_score,
            "yolo_status": scenario.yolo_status,
            "analysis_target": True,
        }
    )
    return records


def generate_mock_fixtures(mock_data_dir: Path) -> None:
    fixtures = mock_data_dir / "fixtures"
    runtime = mock_data_dir / "runtime"
    examples = mock_data_dir / "examples"

    drain_records = [
        {
            "drain_id": scenario.drain_id,
            "drain_code": scenario.drain_code,
            "address": scenario.address,
            "latitude": round(37.55 + (index * 0.002), 7),
            "longitude": round(126.95 + (index * 0.002), 7),
            "status": "active",
        }
        for index, scenario in enumerate(SCENARIOS)
    ]
    yolo_records = [record for scenario in SCENARIOS for record in _yolo_records(scenario)]
    sensor_records = [record for scenario in SCENARIOS for record in _sensor_series(scenario)]
    expected = [
        {
            "yolo_result_id": scenario.yolo_result_id,
            "drain_id": scenario.drain_id,
            "scenario": scenario.address,
            "expected_risk_level": scenario.expected_risk_level,
            "expected_state_code": scenario.expected_state_code,
        }
        for scenario in SCENARIOS
    ]

    _jsonl_write(fixtures / "drain_data.jsonl", drain_records)
    _jsonl_write(fixtures / "yolo_result_data.jsonl", yolo_records)
    _jsonl_write(fixtures / "sensor_data.jsonl", sensor_records)
    _jsonl_write(examples / "expected_outcomes.jsonl", expected)

    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / ".gitkeep").touch()


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    generate_mock_fixtures(root / "mock_data")
    print(f"Mock fixtures generated under: {root / 'mock_data'}")


if __name__ == "__main__":
    main()
