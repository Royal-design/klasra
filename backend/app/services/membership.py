import uuid

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import hash_password
from app.models.membership import SchoolMembership
from app.models.user import User
from app.repositories import membership_repo, user_repo
from app.schemas.membership import MembershipUpdateRequest, SchoolUserCreateRequest
from app.services.audit import record_audit_event
from app.services.auth import revoke_all_user_sessions


def _assert_teacher_single_school(
    db: Session,
    *,
    user_id: uuid.UUID,
    target_school_id: uuid.UUID,
) -> None:
    """AUTH-03: Enforce that a teacher has at most one active school membership."""
    existing = membership_repo.get_active_teacher_membership_elsewhere(
        db, user_id=user_id, exclude_school_id=target_school_id
    )
    if existing is not None:
        raise AppError(
            status_code=409,
            code="TEACHER_SINGLE_SCHOOL_VIOLATION",
            message="A teacher can only be actively associated with one school.",
        )


def create_school_user(
    db: Session,
    *,
    school_id: uuid.UUID,
    payload: SchoolUserCreateRequest,
    actor_user_id: uuid.UUID,
) -> tuple[User, SchoolMembership]:
    """Create a user account (or attach existing) with a role inside one school."""
    user = user_repo.get_user_by_email(db, email=str(payload.email))
    created_new_user = False

    if user is None:
        user = user_repo.create_user(
            db,
            email=str(payload.email),
            full_name=payload.full_name,
            password_hash=hash_password(payload.password),
            is_platform_admin=False,
            is_active=True,
        )
        db.flush()
        created_new_user = True
    else:
        existing_in_school = membership_repo.get_user_membership_in_school(
            db, user_id=user.id, school_id=school_id
        )
        if existing_in_school is not None:
            raise AppError(
                status_code=409,
                code="MEMBERSHIP_EXISTS",
                message="This user already has a membership in this school.",
            )

    if payload.role == "teacher":
        _assert_teacher_single_school(db, user_id=user.id, target_school_id=school_id)

    membership = membership_repo.create_membership(
        db,
        user_id=user.id,
        school_id=school_id,
        role=payload.role,
        status="active",
    )
    db.flush()

    record_audit_event(
        db,
        action="membership.created",
        target_type="school_membership",
        target_id=membership.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={
            "user_id": str(user.id),
            "role": membership.role,
            "status": membership.status,
            "created_new_user": created_new_user,
        },
    )

    db.commit()
    db.refresh(user)
    db.refresh(membership)
    return user, membership


def list_school_users(
    db: Session, *, school_id: uuid.UUID
) -> list[tuple[User, SchoolMembership]]:
    return membership_repo.list_school_users_with_memberships(db, school_id=school_id)


def update_school_membership(
    db: Session,
    *,
    school_id: uuid.UUID,
    membership_id: uuid.UUID,
    payload: MembershipUpdateRequest,
    actor_user_id: uuid.UUID,
) -> tuple[User, SchoolMembership]:
    membership = membership_repo.get_membership_for_school(
        db, school_id=school_id, membership_id=membership_id
    )
    if membership is None:
        raise AppError(
            status_code=404,
            code="MEMBERSHIP_NOT_FOUND",
            message="School membership not found.",
        )

    new_role = payload.role or membership.role
    new_status = payload.status or membership.status

    if new_role == membership.role and new_status == membership.status:
        user = user_repo.get_user_by_id(db, user_id=membership.user_id)
        assert user is not None
        return user, membership

    if membership.status == "revoked" and payload.status == "revoked" and payload.role is None:
        raise AppError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Membership is already revoked.",
        )

    if membership.role == "school_admin" and membership.status == "active":
        losing_admin = new_role != "school_admin" or new_status != "active"
        if losing_admin:
            active_admins_count = membership_repo.count_active_school_admins(
                db, school_id=school_id
            )
            if active_admins_count <= 1:
                raise AppError(
                    status_code=409,
                    code="LAST_SCHOOL_ADMIN",
                    message="Cannot remove or demote the last active school administrator.",
                )

    if new_role == "teacher" and new_status == "active":
        _assert_teacher_single_school(
            db, user_id=membership.user_id, target_school_id=school_id
        )

    previous_role = membership.role
    previous_status = membership.status
    membership.role = new_role
    membership.status = new_status

    if new_status == "revoked":
        revoke_all_user_sessions(db, user_id=membership.user_id)

    record_audit_event(
        db,
        action="membership.updated",
        target_type="school_membership",
        target_id=membership.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={
            "user_id": str(membership.user_id),
            "previous_role": previous_role,
            "new_role": new_role,
            "previous_status": previous_status,
            "new_status": new_status,
        },
    )

    db.commit()
    db.refresh(membership)
    user = user_repo.get_user_by_id(db, user_id=membership.user_id)
    assert user is not None
    return user, membership
