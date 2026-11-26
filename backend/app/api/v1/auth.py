from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import (
    AuthContext,
    get_app_settings,
    get_current_auth,
    get_email_provider,
    verify_csrf,
)
from app.core.config import Settings
from app.db.session import get_db
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MembershipSummary,
    MessageResponse,
    ResetPasswordRequest,
    UserProfile,
)
from app.services.auth import (
    authenticate_user,
    change_user_password,
    create_user_session,
    get_user_memberships,
    request_password_reset,
    reset_password_with_token,
    revoke_all_user_sessions,
)
from app.services.email import EmailProvider

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


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request a password reset email",
)
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    email_provider: EmailProvider = Depends(get_email_provider),
) -> MessageResponse:
    request_password_reset(
        db,
        email=str(payload.email),
        ttl_minutes=settings.password_reset_ttl_minutes,
        frontend_base_url=settings.frontend_base_url,
        email_provider=email_provider,
    )
    return MessageResponse(
        message="If an active account matches that email, a password reset link has been sent."
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password using a single-use token from email",
)
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    reset_password_with_token(
        db,
        raw_token=payload.token,
        new_password=payload.new_password,
    )
    return MessageResponse(
        message="Password has been reset successfully. Please sign in with your new password."
    )


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password for the currently signed-in user",
)
def change_password(
    payload: ChangePasswordRequest,
    response: Response,
    auth: AuthContext = Depends(verify_csrf),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> MessageResponse:
    change_user_password(
        db,
        user=auth.user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    response.delete_cookie(key=settings.session_cookie_name, path="/")
    response.delete_cookie(key=settings.csrf_cookie_name, path="/")
    return MessageResponse(
        message="Password changed successfully. Please sign in again."
    )
