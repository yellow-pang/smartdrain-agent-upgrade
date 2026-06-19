import os
from dataclasses import dataclass


@dataclass(frozen=True)
class HttpSettings:
    backend_base_url: str = "http://localhost:8000"
    callback_timeout_seconds: float = 10.0
    callback_retry_count: int = 1

    @property
    def yolo_callback_url(self) -> str:
        return f"{self.backend_base_url}/api/ai-callback/yolo-result"

    @property
    def xgboost_callback_url(self) -> str:
        return f"{self.backend_base_url}/api/ai-callback/xgboost-result"


def get_http_settings() -> HttpSettings:
    return HttpSettings(
        backend_base_url=os.getenv(
            "BACKEND_BASE_URL",
            "http://localhost:8000",
        ).rstrip("/"),
        callback_timeout_seconds=float(
            os.getenv("BACKEND_CALLBACK_TIMEOUT_SECONDS", "10")
        ),
        callback_retry_count=int(os.getenv("BACKEND_CALLBACK_RETRY_COUNT", "1")),
    )

