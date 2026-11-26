import uuid
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.core.security import constant_time_equals
from app.db.session import get_db
from app.models.membership import SchoolMembership
from app.models.school import School
from app.models.session import UserSession
from app.models.user import User
from app.repositories import membership_repo, school_repo
from app.services.auth import get_active_session_and_user


@dataclass
class AuthContext:
    user: User
    session: UserSession


@dataclass
class SchoolAuthContext:
    user: User
    session: UserSession
    school: School
    membership: SchoolMembership


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_current_auth(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> AuthContext:
    raw_token = request.cookies.get(settings.session_cookie_name)
    if not raw_token:
        raise AppError(
            status_code=401,
            code="AUTHENTICATION_REQUIRED",
            message="Authentication required.",
        )
    session, user = get_active_session_and_user(db, raw_session_token=raw_token)
    return AuthContext(user=user, session=session)


def verify_csrf(
    request: Request,
    auth: AuthContext = Depends(get_current_auth),
) -> AuthContext:
    """Validate X-CSRF-Token header against the session's stored CSRF token hash."""
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return auth

    header_token = request.headers.get("X-CSRF-Token")
    if not header_token or not constant_time_equals(
        auth.session.csrf_token_hash, header_token
    ):
        raise AppError(
            status_code=403,
            code="CSRF_FAILED",
            message="Invalid or missing CSRF token.",
        )
    return auth


def require_platform_admin(
    auth: AuthContext = Depends(verify_csrf),
) -> AuthContext:
    if not auth.user.is_platform_admin:
        raise AppError(
            status_code=403,
            code="FORBIDDEN",
            message="Platform administrator permission required.",
        )
    return auth


def require_school_role(allowed_roles: set[str]) -> Callable[..., SchoolAuthContext]:
    """Enforce school-scoped role authorization (fail closed on cross-school access)."""

    def _dependency(
        school_id: uuid.UUID,
        auth: AuthContext = Depends(verify_csrf),
        db: Session = Depends(get_db),
    ) -> SchoolAuthContext:
        membership = membership_repo.get_user_membership_in_school(
            db, user_id=auth.user.id, school_id=school_id
        )
        if membership is None:
            raise AppError(
                status_code=403,
                code="FORBIDDEN",
                message="You do not have access to this school.",
            )
        if membership.status == "pending":
            raise AppError(
                status_code=403,
                code="MEMBERSHIP_PENDING",
                message="Your school membership is pending approval.",
            )
        if membership.status != "active" or membership.role not in allowed_roles:
            raise AppError(
                status_code=403,
                code="FORBIDDEN",
                message="You do not have permission to perform this action.",
            )

        school = school_repo.get_school_by_id(db, school_id=school_id)
        if school is None or school.status != "active":
            raise AppError(
                status_code=403,
                code="SCHOOL_INACTIVE",
                message="This school is not currently active.",
            )

        return SchoolAuthContext(
            user=auth.user,
            session=auth.session,
            school=school,
            membership=membership,
        )

    return _dependency
