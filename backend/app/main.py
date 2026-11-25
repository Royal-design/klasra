from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    # Disable interactive OpenAPI docs in production by default.
    docs_url = "/docs" if app_settings.app_env != "production" else None
    redoc_url = "/redoc" if app_settings.app_env != "production" else None
    openapi_url = "/openapi.json" if app_settings.app_env != "production" else None

    app = FastAPI(
        title=app_settings.app_name,
        version="0.1.0",
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
    )

    @app.middleware("http")
    async def add_security_headers(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store"
        # Apply strict CSP to API endpoints; FastAPI's local dev /docs loads Swagger assets.
        if request.url.path.startswith(app_settings.api_v1_prefix):
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; frame-ancestors 'none'"
            )
        return response

    app.include_router(api_router, prefix=app_settings.api_v1_prefix)

    return app

