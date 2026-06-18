"""Application service orchestrating repositories, feature engineering, and inference."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from flood_risk_xgb.config import Settings
from flood_risk_xgb.domain import (
    AnalysisStatus,
    AnalysisTrace,
    DataQuality,
    RiskLevel,
    SensorQuality,
    StateCode,
    XgboostResult,
    YoloResult,
)
from flood_risk_xgb.exceptions import InsufficientSensorDataError
from flood_risk_xgb.features.builder import FeatureBuilder
from flood_risk_xgb.inference.predictor import RiskPredictor
from flood_risk_xgb.policy.decision import build_decision_reason, final_decision_for
from flood_risk_xgb.policy.quality_gate import QualityGate
from flood_risk_xgb.policy.sensor_diagnostics import SensorDiagnostics
from flood_risk_xgb.policy.state_interpreter import interpret_state
from flood_risk_xgb.repositories.interfaces import (
    AnalysisTraceRepository,
    SensorRepository,
    XgboostResultRepository,
    YoloResultRepository,
)
from flood_risk_xgb.repositories.jsonl import (
    JsonlAnalysisTraceRepository,
    JsonlSensorRepository,
    JsonlXgboostResultRepository,
    JsonlYoloResultRepository,
)
from flood_risk_xgb.repositories.postgres import build_postgres_repositories


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _worst_quality(left: DataQuality, right: DataQuality) -> DataQuality:
    order = {
        DataQuality.VALID: 0,
        DataQuality.SUSPECT: 1,
        DataQuality.INSUFFICIENT: 2,
        DataQuality.STALE: 3,
        DataQuality.INVALID: 4,
    }
    return left if order[left] >= order[right] else right


def _analysis_status_for(data_quality: DataQuality, can_predict: bool) -> AnalysisStatus:
    if not can_predict:
        return AnalysisStatus.SKIPPED
    if data_quality == DataQuality.VALID:
        return AnalysisStatus.COMPLETED
    return AnalysisStatus.DEGRADED


class AnalysisService:
    def __init__(
        self,
        settings: Settings,
        yolo_repository: YoloResultRepository,
        sensor_repository: SensorRepository,
        result_repository: XgboostResultRepository,
        trace_repository: AnalysisTraceRepository,
        predictor: RiskPredictor,
    ) -> None:
        self.settings = settings
        self.yolo_repository = yolo_repository
        self.sensor_repository = sensor_repository
        self.result_repository = result_repository
        self.trace_repository = trace_repository
        self.predictor = predictor
        self.feature_builder = FeatureBuilder(
            lookback_minutes=settings.sensor_lookback_minutes,
            short_window_minutes=settings.sensor_short_window_minutes,
        )
        self.quality_gate = QualityGate(
            max_sensor_age_seconds=settings.max_sensor_age_seconds,
            min_sensor_count_30m=settings.min_sensor_count_30m,
            min_yolo_confidence=settings.min_yolo_confidence,
            allow_sensor_danger_override=settings.allow_sensor_danger_override,
        )
        self.sensor_diagnostics = SensorDiagnostics(
            max_sensor_age_seconds=settings.max_sensor_age_seconds
        )

    def _load_yolo_history(self, target: YoloResult) -> list[YoloResult]:
        reference_time = _as_utc(target.captured_at)
        window_start = reference_time - timedelta(minutes=self.settings.sensor_lookback_minutes)
        rows: list[YoloResult] = []
        for row in self.yolo_repository.list_all():
            if row.yolo_result_id == target.yolo_result_id:
                continue
            if row.drain_id != target.drain_id:
                continue
            captured_at = _as_utc(row.captured_at)
            if window_start <= captured_at <= reference_time:
                rows.append(row)
        return sorted(rows, key=lambda row: _as_utc(row.captured_at))

    def analyze(self, yolo_result_id: int, force: bool = False) -> XgboostResult:
        existing = self.result_repository.find_latest_by_yolo_result_id(yolo_result_id)
        if existing is not None and not force:
            return existing

        yolo_result = self.yolo_repository.get_by_id(yolo_result_id)
        window_end = yolo_result.captured_at
        window_start = window_end - timedelta(minutes=self.settings.sensor_lookback_minutes)
        sensor_records = self.sensor_repository.list_between(
            drain_id=yolo_result.drain_id,
            start_time=window_start,
            end_time=window_end,
        )
        yolo_history = self._load_yolo_history(yolo_result)

        evaluated_at = datetime.now(timezone.utc)
        feature_values: dict[str, float] | None = None
        class_probabilities: dict[str, float] | None = None
        warnings: list[str] = []
        reason_codes: list[str] = []
        latest_sensor_time: datetime | None = None
        risk_level = RiskLevel.UNKNOWN
        risk_score: float | None = None
        data_quality = DataQuality.VALID
        analysis_status = AnalysisStatus.COMPLETED
        selected_state: StateCode | None = None
        decision_reason = ""

        valid_records = [
            row
            for row in sensor_records
            if row.quality_status == SensorQuality.VALID
            and _as_utc(row.measured_at) <= _as_utc(window_end)
        ]
        if valid_records:
            latest_sensor_time = max(
                valid_records,
                key=lambda row: _as_utc(row.measured_at),
            ).measured_at

        diagnostics = self.sensor_diagnostics.evaluate(sensor_records, window_end)
        warnings.extend(diagnostics.warnings)
        reason_codes.extend(diagnostics.reason_codes)
        data_quality = _worst_quality(data_quality, diagnostics.data_quality)
        selected_state = diagnostics.state_code

        try:
            features = self.feature_builder.build(yolo_result, sensor_records, yolo_history)
            feature_values = features.as_ordered_dict()

            gate = self.quality_gate.evaluate(yolo_result, features)
            warnings.extend(gate.warnings)
            data_quality = _worst_quality(data_quality, gate.data_quality)
            if gate.state_code is not None and selected_state is None:
                selected_state = gate.state_code

            if diagnostics.can_attempt_prediction and gate.can_predict:
                prediction = self.predictor.predict(features)
                risk_level = prediction.risk_level
                risk_score = prediction.risk_score
                class_probabilities = prediction.class_probabilities
                can_predict = True
            else:
                decision_reason = diagnostics.warnings[0] if diagnostics.warnings else gate.reason
                can_predict = False

            interpretation = interpret_state(
                risk_level=risk_level,
                features=features,
                data_quality=data_quality,
                preselected_state=selected_state if not can_predict else diagnostics.state_code,
                preselected_reason_codes=reason_codes,
            )
            state_code = interpretation.state_code
            reason_codes = list(dict.fromkeys(reason_codes + interpretation.reason_codes))
            if can_predict:
                decision_reason = build_decision_reason(
                    risk_level,
                    features,
                    state_code=state_code,
                    reason_codes=reason_codes,
                )
            elif not decision_reason:
                decision_reason = interpretation.decision_reason
            analysis_status = _analysis_status_for(data_quality, can_predict)

        except InsufficientSensorDataError as exc:
            state_code = selected_state or StateCode.NO_VALID_SENSOR_DATA
            data_quality = _worst_quality(data_quality, DataQuality.INVALID)
            analysis_status = AnalysisStatus.SKIPPED
            decision_reason = str(exc)
            if not reason_codes:
                reason_codes = [state_code.value]

        report = XgboostResult(
            drain_id=yolo_result.drain_id,
            sensor_measured_at=latest_sensor_time,
            yolo_result_id=yolo_result.yolo_result_id,
            evaluated_at=evaluated_at,
            risk_score=risk_score,
            risk_level=risk_level,
            final_decision=final_decision_for(risk_level, state_code, data_quality),
            analysis_status=analysis_status,
            data_quality=data_quality,
            state_code=state_code,
            reason_codes=reason_codes,
        )
        persisted = self.result_repository.save(report)

        trace = AnalysisTrace(
            xgboost_id=persisted.xgboost_id,
            yolo_result_id=yolo_result.yolo_result_id,
            drain_id=yolo_result.drain_id,
            sensor_window_start=window_start,
            sensor_window_end=window_end,
            model_version=self.predictor.model_version,
            feature_values=feature_values,
            class_probabilities=class_probabilities,
            decision_reason=decision_reason,
            warnings=warnings,
            analysis_status=analysis_status,
            data_quality=data_quality,
            state_code=state_code,
            reason_codes=reason_codes,
            source_refs={
                "yolo_result_id": yolo_result.yolo_result_id,
                "yolo_history_count": len(yolo_history),
                "sensor_record_count_raw": len(sensor_records),
                "sensor_record_count_valid": len(valid_records),
                "analysis_target": yolo_result.analysis_target,
            },
        )
        self.trace_repository.save(trace)
        return persisted

    def analyze_pending(self) -> list[XgboostResult]:
        processed = self.result_repository.processed_yolo_result_ids()
        results: list[XgboostResult] = []
        for yolo_result in self.yolo_repository.list_all():
            if not yolo_result.analysis_target:
                continue
            if yolo_result.yolo_result_id not in processed:
                results.append(self.analyze(yolo_result.yolo_result_id))
        return results


def build_default_service(settings: Settings | None = None) -> AnalysisService:
    resolved = settings or Settings.from_env()
    predictor = RiskPredictor(resolved.model_path, resolved.model_metadata_path)

    if resolved.data_source == "mock":
        fixtures = resolved.mock_data_dir / "fixtures"
        runtime = resolved.mock_data_dir / "runtime"
        return AnalysisService(
            settings=resolved,
            yolo_repository=JsonlYoloResultRepository(fixtures / "yolo_result_data.jsonl"),
            sensor_repository=JsonlSensorRepository(fixtures / "sensor_data.jsonl"),
            result_repository=JsonlXgboostResultRepository(runtime / "xgboost_data.jsonl"),
            trace_repository=JsonlAnalysisTraceRepository(runtime / "analysis_trace.jsonl"),
            predictor=predictor,
        )

    if resolved.data_source == "postgres":
        if not resolved.database_url:
            raise ValueError("DATABASE_URL is required when DATA_SOURCE=postgres")
        repositories = build_postgres_repositories(resolved.database_url)
        return AnalysisService(settings=resolved, predictor=predictor, **repositories)

    raise ValueError(f"Unsupported DATA_SOURCE: {resolved.data_source}")
