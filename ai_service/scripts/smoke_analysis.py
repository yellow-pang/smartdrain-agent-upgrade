import argparse
import json
from pathlib import Path

from ai_service.analysis.service import run_analysis_job
from ai_service.image_source.service import resolve_image_source_by_drain_id


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
    # backend callback 전송은 http 계층 책임이므로 여기서는 run_analysis_job 결과만 출력한다.
    result = run_analysis_job(payload)
    print("[ANALYSIS_RESULT]")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run local AI analysis smoke without sending backend callbacks.",
    )
    parser.add_argument("--drain-id", type=int, required=True)
    parser.add_argument("--request-id", default="REQ_SMOKE_LOCAL")
    parser.add_argument("--measured-at", default="2026-06-18T08:36:13+09:00")
    parser.add_argument("--water-level-cm", type=float, default=98.13)
    parser.add_argument("--flow-velocity-mps", type=float, default=0.4512)
    return parser.parse_args()


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
