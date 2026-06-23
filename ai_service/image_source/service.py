from .mock_provider import ImageSource, get_mock_image_source_by_drain_id


def resolve_image_source_by_drain_id(drain_id: int | str) -> ImageSource:
    return get_mock_image_source_by_drain_id(drain_id)


def resolve_image_path_by_drain_id(drain_id: int | str) -> str:
    return resolve_image_source_by_drain_id(drain_id).local_path
