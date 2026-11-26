import time
from collections import defaultdict, deque

from fastapi import Request, status
from fastapi.responses import JSONResponse


class SlidingWindowRateLimiter:
    """Simple per-IP sliding-window rate limiter (60-second window).

    TODO(security): Replace with a shared Redis-backed rate limiter when running
    multiple backend instances in staging/production.
    """

    def __init__(self, general_limit: int, login_limit: int, login_path: str) -> None:
        self.general_limit = general_limit
        self.login_limit = login_limit
        self.login_path = login_path
        self._buckets: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    def check(self, request: Request) -> JSONResponse | None:
        client_ip = request.client.host if request.client else "unknown"
        is_login = request.url.path == self.login_path and request.method == "POST"
        bucket_name = "login" if is_login else "general"
        limit = self.login_limit if is_login else self.general_limit

        now = time.monotonic()
        window_start = now - 60.0
        bucket = self._buckets[(client_ip, bucket_name)]

        while bucket and bucket[0] <= window_start:
            bucket.popleft()

        if len(bucket) >= limit:
            retry_after = max(1, int(60 - (now - bucket[0])))
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": "Too many requests. Please try again shortly.",
                        "details": [],
                    }
                },
                headers={"Retry-After": str(retry_after)},
            )

        bucket.append(now)
        return None
