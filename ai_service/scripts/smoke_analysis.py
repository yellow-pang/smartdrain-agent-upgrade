import argparse
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path

from ai_service.analysis.decision_mapper import BACKEND_FINAL_DECISION_BY_RISK_LEVEL
from ai_service.analysis.job_id import build_job_id
from ai_service.analysis.service import run_analysis_job
from ai_service.image_source.service import resolve_image_source_by_drain_id
from ai_service.xgboost.model_predictor import DEFAULT_XGBOOST_MODEL_PATH
from ai_service.yolo.analyzer import DEFAULT_YOLO_MODEL_PATH
from ai_service.yolo.contract import validate_yolo_result_contract


REFERENCE_MEASURED_AT = "2026-06-18T08:36:13+09:00"
REFERENCE_WATER_LEVEL_CM = 98.13
REFERENCE_FLOW_VELOCITY_MPS = 0.4512


def main() -> int:
    args = _parse_args()

    try:
        image_source = resolve_image_source_by_drain_id(args.drain_id)
    except ValueError as exc:
        print(f"[ERROR] image source resolve failed: {exc}")
        return 1

    print("[IMAGE_SOURCE]")
    print(json.dumps(_image_source_to_dict(image_source), ensure_ascii=False, indent=2))

    local_path = Path(image_source.local_path)
    if not local_path.exists():
        print(
            "[SKIP] local_path image file does not exist. "
            "Place a mock CCTV image at this path before running real YOLO smoke."
        )
        print(f"[SKIP] missing local_path: {local_path}")
        print("[HINT] run: python -m ai_service.scripts.check_samples")
        return 2

    payload = _build_payload(args)
    print("[REQUEST_PAYLOAD]")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    # 이 스크립트는 모델 실행 smoke만 확인한다.
    # backend callback 전송은 http 계층 책임이며 여기서는 운영 DB를 변경하지 않는다.
    try:
        if args.verify_reference:
            _verify_artifacts(args, local_path)
        result = run_analysis_job(payload)
        if args.verify_reference:
            _verify_reference_result(result, payload, args)
    except Exception as exc:
        print(f"[ERROR] analysis smoke failed: {type(exc).__name__}: {exc}")
        return 1

    print("[ANALYSIS_RESULT]")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.verify_reference:
        print("[PASS] reference artifacts and inference result verified")
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run local AI analysis smoke without sending backend callbacks.",
    )
    parser.add_argument("--drain-id", type=int, required=True)
    parser.add_argument("--request-id", default="REQ_SMOKE_LOCAL")
    parser.add_argument("--measured-at", default=REFERENCE_MEASURED_AT)
    parser.add_argument("--water-level-cm", type=float, default=REFERENCE_WATER_LEVEL_CM)
    parser.add_argument("--flow-velocity-mps", type=float, default=REFERENCE_FLOW_VELOCITY_MPS)
    parser.add_argument(
        "--verify-reference", action="store_true",
        help="Verify fixed drain 2 inputs against explicitly approved hashes and classifications.",
    )
    parser.add_argument("--expected-yolo-sha256", type=_sha256_argument)
    parser.add_argument("--expected-sample-sha256", type=_sha256_argument)
    parser.add_argument("--expected-xgboost-sha256", type=_sha256_argument)
    parser.add_argument("--expected-yolo-status", choices=("good", "dirty", "blocked"))
    parser.add_argument("--expected-risk-level", choices=tuple(BACKEND_FINAL_DECISION_BY_RISK_LEVEL))
    parser.add_argument("--expected-final-decision", choices=tuple(BACKEND_FINAL_DECISION_BY_RISK_LEVEL.values()))
    args = parser.parse_args()
    reference_fields = (
        "expected_yolo_sha256", "expected_sample_sha256", "expected_xgboost_sha256",
        "expected_yolo_status", "expected_risk_level", "expected_final_decision",
    )
    if args.verify_reference:
        missing = [f"--{name.replace('_', '-')}" for name in reference_fields if getattr(args, name) is None]
        if missing:
            parser.error(f"--verify-reference requires: {', '.join(missing)}")
        if (
            args.drain_id != 2
            or args.measured_at != REFERENCE_MEASURED_AT
            or args.water_level_cm != REFERENCE_WATER_LEVEL_CM
            or args.flow_velocity_mps != REFERENCE_FLOW_VELOCITY_MPS
        ):
            parser.error("--verify-reference requires drain 2 and the default measured-at/sensor inputs")
        if BACKEND_FINAL_DECISION_BY_RISK_LEVEL[args.expected_risk_level] != args.expected_final_decision:
            parser.error("expected risk level and final decision do not match the existing service contract")
    elif any(getattr(args, name) is not None for name in reference_fields):
        parser.error("expected reference values require --verify-reference")
    return args


def _sha256_argument(value: str) -> str:
    if len(value) != 64 or any(character not in "0123456789abcdefABCDEF" for character in value):
        raise argparse.ArgumentTypeError("SHA256 must contain exactly 64 hexadecimal characters")
    return value.lower()


def _verify_artifacts(args: argparse.Namespace, sample_path: Path) -> None:
    artifacts = (
        ("YOLO model", DEFAULT_YOLO_MODEL_PATH, args.expected_yolo_sha256),
        ("sample", sample_path, args.expected_sample_sha256),
        ("XGBoost model", DEFAULT_XGBOOST_MODEL_PATH, args.expected_xgboost_sha256),
    )
    for name, path, expected_hash in artifacts:
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"{name} must be a non-empty regular file")
        digest = hashlib.sha256()
        with path.open("rb") as artifact:
            for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected_hash:
            raise ValueError(f"{name} SHA256 does not match the approved reference")


def _verify_reference_result(result: dict, payload: dict, args: argparse.Namespace) -> None:
    if not isinstance(result, dict):
        raise ValueError("analysis result must be a dict")
    expected_job_id = build_job_id(payload["request_id"])
    for key in ("accepted_response", "yolo_callback_payload", "xgboost_callback_payload"):
        response = result.get(key)
        if not isinstance(response, dict):
            raise ValueError(f"missing or invalid {key}")
        if response.get("request_id") != payload["request_id"] or response.get("job_id") != expected_job_id:
            raise ValueError(f"{key} request/job identifiers do not match")
    accepted = result["accepted_response"]
    if accepted.get("accepted") is not True or accepted.get("status") != "processing":
        raise ValueError("accepted response must retain accepted=true and status=processing")

    yolo = result["yolo_callback_payload"].get("yolo_result")
    validate_yolo_result_contract(yolo)
    if yolo["yolo_status"] != args.expected_yolo_status:
        raise ValueError("YOLO classification does not match the approved reference (unknown sentinel is not success)")

    xgboost = result["xgboost_callback_payload"].get("xgboost_result")
    if not isinstance(xgboost, dict):
        raise ValueError("missing or invalid xgboost_result")
    score = xgboost.get("risk_score")
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= 1:
        raise ValueError("XGBoost risk_score must be a finite number between 0 and 1")
    if xgboost.get("risk_level") != args.expected_risk_level or xgboost.get("final_decision") != args.expected_final_decision:
        raise ValueError("XGBoost classification/final decision does not match the approved reference")
    evaluated_at = xgboost.get("evaluated_at")
    if not isinstance(evaluated_at, str) or datetime.fromisoformat(evaluated_at).utcoffset() is None:
        raise ValueError("XGBoost evaluated_at must be an ISO datetime with timezone")


def _build_payload(args: argparse.Namespace) -> dict:
    return {
        "request_id": args.request_id,
        "drain_id": args.drain_id,
        "sensor_data": {
            "measured_at": args.measured_at,
            "water_level_cm": args.water_level_cm,
            "flow_velocity_mps": args.flow_velocity_mps,
            "quality_status": "valid",
        },
    }


def _image_source_to_dict(image_source) -> dict:
    return {
        "drain_id": image_source.drain_id,
        "source_url": image_source.source_url,
        "local_path": image_source.local_path,
    }


if __name__ == "__main__":
    raise SystemExit(main())
