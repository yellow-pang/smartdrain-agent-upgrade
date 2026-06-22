from dataclasses import dataclass

from .constants import MOCK_IMAGE_SOURCE_BY_DRAIN_ID


@dataclass(frozen=True)
class ImageSource:
    drain_id: int
    source_url: str
    local_path: str


def get_mock_image_source_by_drain_id(drain_id: int) -> ImageSource:
    try:
        source = MOCK_IMAGE_SOURCE_BY_DRAIN_ID[int(drain_id)]
    except (KeyError, TypeError, ValueError) as exc:
        # mock에 없는 drain_id는 단순 미탐지가 아니라 CCTV/스토리지 소스 설정 문제로 본다.
        # 현재 정책은 unknown 결과를 만들지 않고 요청 단계에서 실패시키는 것이다.
        raise ValueError(f"No mock image source configured for drain_id: {drain_id}") from exc

    return ImageSource(
        drain_id=int(drain_id),
        source_url=source["source_url"],
        local_path=source["local_path"],
    )
