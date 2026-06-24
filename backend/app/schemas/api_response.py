"""
프론트엔드 API 명세에 맞춘 공통 응답과 DTO 변환을 제공하는 파일입니다.

주요 역할:
- REST API 공통 wrapper 응답 생성
- SQLAlchemy 모델을 camelCase DTO 딕셔너리로 변환
- 하수구 상세와 최신 분석 응답 구성
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.drain import Drain
from app.models.sensor_data import SensorData
from app.models.xgboost_result import XgboostResult
from app.models.yolo_result import YoloResult
from app.websocket.events import DRAIN_STATUS_UPDATED

KST = timezone(timedelta(hours=9))
RISK_LEVELS = {"good", "caution", "danger", "unknown"}
YOLO_STATUSES = {"clear", "partially_blocked", "blocked", "unknown"}


def now_timestamp() -> str:
    return datetime.now(KST).isoformat()


def format_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(KST).isoformat()


def normalize_risk_level(value: str | None) -> str:
    return value if value in RISK_LEVELS else "unknown"


def normalize_yolo_status(value: str | None) -> str:
    if value == "good":
        return "clear"
    if value == "dirty":
        return "partially_blocked"
    return value if value in YOLO_STATUSES else "unknown"


def api_response(data: Any, message: str | None = None, error: Any = None, success: bool = True) -> dict[str, Any]:
    return {
        "success": success,
        "data": data,
        "message": message,
        "error": error,
        "timestamp": now_timestamp(),
    }


def api_error_response(code: str, message: str, detail: Any | None = None) -> dict[str, Any]:
    return api_response(
        data=None,
        message="요청 처리 중 오류가 발생했습니다.",
        error={"code": code, "message": message, "detail": detail or {}},
        success=False,
    )


def api_list_response(items: list[dict[str, Any]], message: str | None = None) -> dict[str, Any]:
    return api_response(data={"items": items, "totalCount": len(items)}, message=message)


def sensor_summary_dto(sensor_data: SensorData | None) -> dict[str, Any] | None:
    if sensor_data is None:
        return None
    return {
        "waterLevelCm": sensor_data.water_level_cm,
        "flowVelocityMps": sensor_data.flow_velocity_mps,
        "measuredAt": format_datetime(sensor_data.measured_at),
    }


def sensor_data_dto(sensor_data: SensorData | None) -> dict[str, Any] | None:
    if sensor_data is None:
        return None
    data = sensor_summary_dto(sensor_data) or {}
    data.update(
        {
            "id": sensor_data.id,
            "drainId": sensor_data.drain.drain_code if sensor_data.drain else sensor_data.drain_id,
            "createdAt": format_datetime(sensor_data.created_at),
        }
    )
    return data


def sensor_history_dto(sensor_data: SensorData | None) -> dict[str, Any] | None:
    if sensor_data is None:
        return None
    return {
        "measuredAt": format_datetime(sensor_data.measured_at),
        "waterLevelCm": sensor_data.water_level_cm,
        "flowVelocityMps": sensor_data.flow_velocity_mps,
    }


def yolo_result_dto(yolo_result: YoloResult | None) -> dict[str, Any] | None:
    if yolo_result is None:
        return None
    return {
        "id": yolo_result.id,
        "drainId": yolo_result.drain.drain_code if yolo_result.drain else yolo_result.drain_id,
        "imageUrl": yolo_result.image_url,
        "obstructionRatio": yolo_result.obstruction_ratio,
        "confidenceScore": yolo_result.confidence_score,
        "yoloStatus": normalize_yolo_status(yolo_result.yolo_status),
        "analyzedAt": format_datetime(yolo_result.created_at),
        "capturedAt": format_datetime(yolo_result.captured_at),
        "createdAt": format_datetime(yolo_result.created_at),
    }


def xgboost_result_dto(result: XgboostResult | None) -> dict[str, Any] | None:
    if result is None:
        return None
    return {
        "id": result.id,
        "drainId": result.drain.drain_code if result.drain else result.drain_id,
        "sensorDataId": result.sensor_data_id,
        "yoloResultId": result.yolo_result_id,
        "riskScore": result.risk_score,
        "riskLevel": normalize_risk_level(result.risk_level),
        "finalDecision": result.final_decision,
        "predictedAt": format_datetime(result.evaluated_at),
        "evaluatedAt": format_datetime(result.evaluated_at),
        "createdAt": format_datetime(result.created_at),
    }


def risk_history_dto(result: XgboostResult | None) -> dict[str, Any] | None:
    if result is None:
        return None
    return {
        "changedAt": format_datetime(result.evaluated_at),
        "riskLevel": normalize_risk_level(result.risk_level),
        "riskScore": result.risk_score,
    }


def latest_sensor_data(db: Session, drain_id: int) -> SensorData | None:
    return (
        db.query(SensorData)
        .filter(SensorData.drain_id == drain_id)
        .order_by(SensorData.measured_at.desc())
        .first()
    )


def latest_yolo_result(db: Session, drain_id: int) -> YoloResult | None:
    results = (
        db.query(YoloResult)
        .filter(YoloResult.drain_id == drain_id)
        .order_by(YoloResult.id.desc())
        .all()
    )
    if not results:
        return None
    return max(results, key=_yolo_latest_sort_key)


def _yolo_latest_sort_key(yolo_result: YoloResult) -> tuple[datetime, datetime]:
    captured_at = getattr(yolo_result, "captured_at", None)
    created_at = getattr(yolo_result, "created_at", None)
    return (_datetime_sort_value(captured_at or created_at), _datetime_sort_value(created_at))


def _datetime_sort_value(value: datetime | None) -> datetime:
    if value is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _yolo_image_url(yolo_result: YoloResult | None) -> str | None:
    if yolo_result is None:
        return None
    value = getattr(yolo_result, "image_url", None) or getattr(yolo_result, "image_uri", None)
    return value or None


def _yolo_captured_at(yolo_result: YoloResult | None) -> datetime | None:
    if yolo_result is None:
        return None
    return getattr(yolo_result, "captured_at", None)


def latest_xgboost_result(db: Session, drain_id: int) -> XgboostResult | None:
    return (
        db.query(XgboostResult)
        .filter(XgboostResult.drain_id == drain_id)
        .order_by(XgboostResult.evaluated_at.desc())
        .first()
    )


def drain_list_item_dto(db: Session, drain: Drain) -> dict[str, Any]:
    sensor_data = latest_sensor_data(db, drain.id)
    yolo_result = latest_yolo_result(db, drain.id)
    xgboost_result = latest_xgboost_result(db, drain.id)
    updated_at = xgboost_result.evaluated_at if xgboost_result else drain.updated_at
    latest_image_url = _yolo_image_url(yolo_result)
    return {
        "id": drain.drain_code,
        "roadAddress": drain.address,
        "fullAddress": drain.address,
        "latitude": drain.latitude,
        "longitude": drain.longitude,
        "riskLevel": normalize_risk_level(xgboost_result.risk_level if xgboost_result else drain.status),
        "riskScore": xgboost_result.risk_score if xgboost_result else None,
        "obstructionRatio": yolo_result.obstruction_ratio if yolo_result else None,
        "waterLevelCm": sensor_data.water_level_cm if sensor_data else None,
        "flowVelocityMps": sensor_data.flow_velocity_mps if sensor_data else None,
        "finalDecision": xgboost_result.final_decision if xgboost_result else None,
        "updatedAt": format_datetime(updated_at),
        "latestImageUrl": latest_image_url,
        "latestImageCapturedAt": format_datetime(_yolo_captured_at(yolo_result)) if latest_image_url else None,
    }


def drain_detail_dto(db: Session, drain: Drain) -> dict[str, Any]:
    sensor_history = (
        db.query(SensorData)
        .filter(SensorData.drain_id == drain.id)
        .order_by(SensorData.measured_at.desc())
        .all()
    )
    risk_history = (
        db.query(XgboostResult)
        .filter(XgboostResult.drain_id == drain.id)
        .order_by(XgboostResult.evaluated_at.desc())
        .all()
    )
    latest_sensor = sensor_history[0] if sensor_history else None
    latest_yolo = latest_yolo_result(db, drain.id)
    latest_xgboost = risk_history[0] if risk_history else None
    detail = drain_list_item_dto(db, drain)
    detail.update(
        {
            "imageUrl": latest_yolo.image_url if latest_yolo else None,
            "sensorSummary": sensor_summary_dto(latest_sensor),
            "sensorHistory": [sensor_history_dto(item) for item in sensor_history],
            "yoloResult": yolo_result_dto(latest_yolo),
            "xgboostResult": xgboost_result_dto(latest_xgboost),
            "riskHistory": [risk_history_dto(item) for item in risk_history],
        }
    )
    return detail


def analysis_latest_dto(db: Session, drain: Drain) -> dict[str, Any]:
    sensor_data = latest_sensor_data(db, drain.id)
    yolo_result = latest_yolo_result(db, drain.id)
    xgboost_result = latest_xgboost_result(db, drain.id)
    return {
        "sensorSummary": sensor_summary_dto(sensor_data),
        "yoloResult": yolo_result_dto(yolo_result),
        "xgboostResult": xgboost_result_dto(xgboost_result),
        "updatedAt": format_datetime(xgboost_result.evaluated_at if xgboost_result else drain.updated_at),
        "drainId": drain.drain_code,
        "riskLevel": normalize_risk_level(xgboost_result.risk_level if xgboost_result else drain.status),
        "riskScore": xgboost_result.risk_score if xgboost_result else None,
        "waterLevelCm": sensor_data.water_level_cm if sensor_data else None,
        "flowVelocityMps": sensor_data.flow_velocity_mps if sensor_data else None,
        "obstructionRatio": yolo_result.obstruction_ratio if yolo_result else None,
        "finalDecision": xgboost_result.final_decision if xgboost_result else None,
        "sensorData": sensor_data_dto(sensor_data),
    }


def drain_status_event_payload(
    db: Session,
    drain: Drain,
    result: XgboostResult,
    sensor_data: SensorData | None = None,
    yolo_result: YoloResult | None = None,
) -> dict[str, Any]:
    sensor_data = sensor_data or latest_sensor_data(db, drain.id)
    yolo_result = yolo_result or latest_yolo_result(db, drain.id)
    return {
        "type": DRAIN_STATUS_UPDATED,
        "payload": {
            "drainId": drain.drain_code,
            "riskLevel": normalize_risk_level(result.risk_level),
            "riskScore": result.risk_score,
            "waterLevelCm": sensor_data.water_level_cm if sensor_data else None,
            "flowVelocityMps": sensor_data.flow_velocity_mps if sensor_data else None,
            "obstructionRatio": yolo_result.obstruction_ratio if yolo_result else None,
            "finalDecision": result.final_decision,
            "updatedAt": format_datetime(result.evaluated_at),
            "sensorDataId": result.sensor_data_id,
            "yoloResultId": result.yolo_result_id,
            "xgboostResultId": result.id,
        },
    }
