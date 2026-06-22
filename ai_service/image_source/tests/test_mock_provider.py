import pytest

from ai_service.image_source.constants import MOCK_IMAGE_SOURCE_BY_DRAIN_ID
from ai_service.image_source.mock_provider import get_mock_image_source_by_drain_id
from ai_service.image_source.service import (
    resolve_image_path_by_drain_id,
    resolve_image_source_by_drain_id,
)


def test_mock_provider_has_five_drain_sources():
    assert set(MOCK_IMAGE_SOURCE_BY_DRAIN_ID) == {1, 2, 3, 4, 5}


@pytest.mark.parametrize("drain_id", [1, 2, 3, 4, 5])
def test_mock_source_contains_future_url_and_local_path(drain_id):
    source = get_mock_image_source_by_drain_id(drain_id)

    assert source.drain_id == drain_id
    assert source.source_url == f"mock://storage/drain-{drain_id}-latest.jpg"
    assert source.local_path.endswith(f"drain_{drain_id}.jpg")


def test_unregistered_or_broken_cctv_source_drain_id_raises_value_error():
    with pytest.raises(ValueError):
        get_mock_image_source_by_drain_id(999)


def test_service_returns_image_source_and_path():
    source = resolve_image_source_by_drain_id(1)

    assert resolve_image_path_by_drain_id(1) == source.local_path
