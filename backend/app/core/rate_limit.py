import time
from collections import defaultdict, deque

from fastapi import Request, status
from fastapi.responses import JSONResponse


class SlidingWindowRateLimiter:
    """Simple per-IP sliding-window rate limiter (60-second window).

    TODO(security): Replace with a shared Redis-backed rate limiter when running
    multiple backend instances in staging/production.
    """

    def __init__(
        self, general_limit: int, auth_limit: int, strict_auth_paths: set[str]
    ) -> None:
        self.general_limit = general_limit
        self.auth_limit = auth_limit
        self.strict_auth_paths = strict_auth_paths
        self._buckets: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    def check(self, request: Request) -> JSONResponse | None:
        client_ip = request.client.host if request.client else "unknown"
        is_strict_auth = (
            request.url.path in self.strict_auth_paths and request.method == "POST"
        )
        bucket_name = "auth" if is_strict_auth else "general"
        limit = self.auth_limit if is_strict_auth else self.general_limit

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
