import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.rate_limit import SlidingWindowRateLimiter
from app.services.email import EmailProvider, build_email_provider
from app.services.file_storage import StorageBackend, build_storage_backend

access_logger = logging.getLogger("app.access")


def create_app(
    settings: Settings | None = None,
    email_provider: EmailProvider | None = None,
    storage_backend: StorageBackend | None = None,
) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging(app_env=app_settings.app_env)

    # Disable interactive OpenAPI docs in production by default.
    docs_url = "/docs" if app_settings.app_env != "production" else None
    redoc_url = "/redoc" if app_settings.app_env != "production" else None
    openapi_url = "/openapi.json" if app_settings.app_env != "production" else None

    app = FastAPI(
        title=app_settings.app_name,
        version="1.0.0",
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )
    app.state.settings = app_settings
    app.state.email_provider = email_provider or build_email_provider(app_settings)
    app.state.storage_backend = storage_backend or build_storage_backend(app_settings)

    register_exception_handlers(app)

    rate_limiter = SlidingWindowRateLimiter(
        general_limit=app_settings.rate_limit_per_minute,
        auth_limit=app_settings.login_rate_limit_per_minute,
        strict_auth_paths={
            f"{app_settings.api_v1_prefix}/auth/login",
            f"{app_settings.api_v1_prefix}/auth/forgot-password",
            f"{app_settings.api_v1_prefix}/auth/reset-password",
            f"{app_settings.api_v1_prefix}/registrations/students",
            f"{app_settings.api_v1_prefix}/staff-invitations/accept",
            f"{app_settings.api_v1_prefix}/guardian-links/verify",
        },
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
    )

    @app.middleware("http")
    async def rate_limit_logging_and_security_headers(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = uuid.uuid4().hex
        start = time.monotonic()

        limited = rate_limiter.check(request)
        if limited is not None:
            response = limited
        else:
            response = await call_next(request)

        duration_ms = round((time.monotonic() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store"
        # Apply strict CSP to API endpoints; FastAPI's local dev /docs loads Swagger assets.
        if request.url.path.startswith(app_settings.api_v1_prefix):
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; frame-ancestors 'none'"
            )

        # Log path only (never query params, cookies, or headers) to stay PII/token-safe.
        access_logger.info(
            "http_request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

    app.include_router(api_router, prefix=app_settings.api_v1_prefix)

    return app
