"""JSONL repositories used before the shared PostgreSQL database is ready."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from flood_risk_xgb.domain import AnalysisTrace, SensorRecord, XgboostResult, YoloResult
from flood_risk_xgb.exceptions import RecordNotFoundError

TModel = TypeVar("TModel", bound=BaseModel)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class JsonlFile:
    def __init__(self, path: Path) -> None:
        self.path = path

    def read_dicts(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line_number, raw_line in enumerate(
            self.path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            line = raw_line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {self.path}:{line_number}") from exc
        return rows

    def write_dicts(self, rows: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
        temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        temp_path.write_text(payload, encoding="utf-8")
        temp_path.replace(self.path)

    def append_model(self, model: BaseModel) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = model.model_dump(mode="json", by_alias=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def clear(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")


class JsonlYoloResultRepository:
    def __init__(self, path: Path) -> None:
        self.store = JsonlFile(path)

    def list_all(self) -> list[YoloResult]:
        rows = [YoloResult.model_validate(row) for row in self.store.read_dicts()]
        return sorted(rows, key=lambda row: row.yolo_result_id)

    def get_by_id(self, yolo_result_id: int) -> YoloResult:
        for row in self.list_all():
            if row.yolo_result_id == yolo_result_id:
                return row
        raise RecordNotFoundError(f"YOLO result not found: {yolo_result_id}")


class JsonlSensorRepository:
    def __init__(self, path: Path) -> None:
        self.store = JsonlFile(path)

    def list_between(
        self,
        drain_id: int,
        start_time: datetime,
        end_time: datetime,
    ) -> list[SensorRecord]:
        start_utc = _as_utc(start_time)
        end_utc = _as_utc(end_time)
        records = [SensorRecord.model_validate(row) for row in self.store.read_dicts()]
        selected = [
            row
            for row in records
            if row.drain_id == drain_id
            and start_utc <= _as_utc(row.measured_at) <= end_utc
        ]
        return sorted(selected, key=lambda row: _as_utc(row.measured_at))


class JsonlXgboostResultRepository:
    def __init__(self, path: Path) -> None:
        self.store = JsonlFile(path)

    def _list_all(self) -> list[XgboostResult]:
        return [XgboostResult.model_validate(row) for row in self.store.read_dicts()]

    def find_latest_by_yolo_result_id(self, yolo_result_id: int) -> XgboostResult | None:
        matching = [
            row for row in self._list_all() if row.yolo_result_id == yolo_result_id
        ]
        if not matching:
            return None
        return max(matching, key=lambda row: _as_utc(row.evaluated_at))

    def processed_yolo_result_ids(self) -> set[int]:
        return {row.yolo_result_id for row in self._list_all()}

    def save(self, result: XgboostResult) -> XgboostResult:
        existing = self._list_all()
        next_id = max((row.xgboost_id or 0 for row in existing), default=0) + 1
        persisted = result.model_copy(update={"xgboost_id": result.xgboost_id or next_id})
        self.store.append_model(persisted)
        return persisted

    def clear(self) -> None:
        self.store.clear()


class JsonlAnalysisTraceRepository:
    def __init__(self, path: Path) -> None:
        self.store = JsonlFile(path)

    def save(self, trace: AnalysisTrace) -> AnalysisTrace:
        self.store.append_model(trace)
        return trace

    def clear(self) -> None:
        self.store.clear()
