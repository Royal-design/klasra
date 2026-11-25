import logging

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Check API and database health",
    responses={
        status.HTTP_200_OK: {"description": "Service and database are healthy"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Database is unavailable"},
    },
)
def health_check(db: Session = Depends(get_db)) -> JSONResponse:
    """Verify the API is running and can execute a basic database query.

    Note: This is an intentionally unauthenticated liveness/readiness endpoint.
    TODO(security): Add API rate limiting middleware across all endpoints (including /health)
    and authentication/authorization on all non-health endpoints starting in Slice 2.
    """
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("Database health check failed")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "degraded", "database": "unavailable"},
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "ok", "database": "ok"},
    )
