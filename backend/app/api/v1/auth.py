from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_app_settings, get_current_auth, verify_csrf
from app.core.config import Settings
from app.db.session import get_db
from app.schemas.auth import LoginRequest, LoginResponse, MembershipSummary, UserProfile
from app.services.auth import (
    authenticate_user,
    create_user_session,
    get_user_memberships,
    revoke_all_user_sessions,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _build_user_profile(db: Session, user) -> UserProfile:
    memberships = get_user_memberships(db, user_id=user.id)
    return UserProfile(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_platform_admin=user.is_platform_admin,
        is_active=user.is_active,
        memberships=[MembershipSummary.model_validate(m) for m in memberships],
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Sign in with email and password",
)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> LoginResponse:
    user = authenticate_user(db, email=str(payload.email), password=payload.password)
    _session, raw_session_token, raw_csrf_token = create_user_session(
        db, user=user, ttl_hours=settings.session_ttl_hours
    )

    max_age_seconds = settings.session_ttl_hours * 3600
    response.set_cookie(
        key=settings.session_cookie_name,
        value=raw_session_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
        max_age=max_age_seconds,
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=raw_csrf_token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
        max_age=max_age_seconds,
    )

    return LoginResponse(
        user=_build_user_profile(db, user),
        csrf_token=raw_csrf_token,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Sign out and invalidate all active sessions",
)
def logout(
    response: Response,
    auth: AuthContext = Depends(verify_csrf),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> Response:
    revoke_all_user_sessions(db, user_id=auth.user.id)
    db.commit()

    response.delete_cookie(key=settings.session_cookie_name, path="/")
    response.delete_cookie(key=settings.csrf_cookie_name, path="/")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Return the authenticated user and school memberships",
)
def get_me(
    auth: AuthContext = Depends(get_current_auth),
    db: Session = Depends(get_db),
) -> UserProfile:
    return _build_user_profile(db, auth.user)
