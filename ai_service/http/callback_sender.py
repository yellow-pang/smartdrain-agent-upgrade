import json
import logging
from urllib import error, request

LOGGER = logging.getLogger(__name__)


def send_json_callback(
    url: str,
    payload: dict,
    timeout_seconds: float,
    retry_count: int,
    *,
    callback_name: str | None = None,
    request_id: str | None = None,
    job_id: str | None = None,
) -> bool:
    callback_label = callback_name or _callback_name_from_url(url)
    max_attempts = retry_count + 1
    for attempt in range(retry_count + 1):
        try:
            _post_json(url, payload, timeout_seconds)
            return True
        except (OSError, error.URLError, error.HTTPError) as exc:
            LOGGER.warning(
                (
                    "Callback delivery failed: callback=%s request_id=%s "
                    "job_id=%s url=%s attempt=%s/%s error_type=%s error=%s"
                ),
                callback_label,
                request_id or payload.get("request_id"),
                job_id or payload.get("job_id"),
                url,
                attempt + 1,
                max_attempts,
                type(exc).__name__,
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


def _callback_name_from_url(url: str) -> str:
    if "yolo-result" in url:
        return "yolo"
    if "xgboost-result" in url:
        return "xgboost"
    return "unknown"
