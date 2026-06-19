import json
import logging
from urllib import error, request

LOGGER = logging.getLogger(__name__)


def send_json_callback(
    url: str,
    payload: dict,
    timeout_seconds: float,
    retry_count: int,
) -> bool:
    for attempt in range(retry_count + 1):
        try:
            _post_json(url, payload, timeout_seconds)
            return True
        except (OSError, error.URLError, error.HTTPError) as exc:
            LOGGER.warning(
                "Callback delivery failed: url=%s attempt=%s/%s error=%s",
                url,
                attempt + 1,
                retry_count + 1,
                exc,
            )

    return False


def _post_json(url: str, payload: dict, timeout_seconds: float) -> None:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=timeout_seconds) as response:
        response.read()

