import json
from pathlib import Path

from ai_service.image_source.constants import MOCK_IMAGE_SOURCE_BY_DRAIN_ID


def main() -> int:
    rows = _build_sample_status_rows()
    missing_rows = [row for row in rows if not row["exists"]]

    print("[SAMPLE_STATUS]")
    print(json.dumps(rows, ensure_ascii=False, indent=2))

    if missing_rows:
        print("[MISSING_SAMPLES]")
        for row in missing_rows:
            print(f"- drain_id={row['drain_id']} local_path={row['local_path']}")
        return 1

    print("[OK] all mock sample images exist.")
    return 0


def _build_sample_status_rows() -> list[dict]:
    rows = []
    for drain_id in sorted(MOCK_IMAGE_SOURCE_BY_DRAIN_ID):
        source = MOCK_IMAGE_SOURCE_BY_DRAIN_ID[drain_id]
        local_path = Path(source["local_path"])
        # 실제 YOLO smoke는 local_path 파일이 있어야만 실행된다.
        # 이 스크립트는 모델을 로드하지 않고 샘플 배치 상태만 빠르게 확인한다.
        rows.append(
            {
                "drain_id": drain_id,
                "source_url": source["source_url"],
                "local_path": str(local_path),
                "exists": local_path.exists(),
            }
        )
    return rows


if __name__ == "__main__":
    raise SystemExit(main())
