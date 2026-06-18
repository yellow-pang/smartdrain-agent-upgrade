"""Repository protocols keep model logic independent from JSONL and PostgreSQL."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from flood_risk_xgb.domain import AnalysisTrace, SensorRecord, XgboostResult, YoloResult


class YoloResultRepository(Protocol):
    def get_by_id(self, yolo_result_id: int) -> YoloResult: ...

    def list_all(self) -> list[YoloResult]: ...


class SensorRepository(Protocol):
    def list_between(
        self,
        drain_id: int,
        start_time: datetime,
        end_time: datetime,
    ) -> list[SensorRecord]: ...


class XgboostResultRepository(Protocol):
    def find_latest_by_yolo_result_id(self, yolo_result_id: int) -> XgboostResult | None: ...

    def processed_yolo_result_ids(self) -> set[int]: ...

    def save(self, result: XgboostResult) -> XgboostResult: ...

    def clear(self) -> None: ...


class AnalysisTraceRepository(Protocol):
    def save(self, trace: AnalysisTrace) -> AnalysisTrace: ...

    def clear(self) -> None: ...
