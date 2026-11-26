import uuid

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import hash_password
from app.models.membership import SchoolMembership
from app.models.school import School
from app.models.user import User
from app.repositories import membership_repo, school_repo, user_repo
from app.schemas.school import SchoolCreateRequest, SchoolUpdateRequest
from app.services.audit import record_audit_event


def create_school_with_admin(
    db: Session,
    *,
    payload: SchoolCreateRequest,
    actor_user_id: uuid.UUID,
) -> tuple[School, User, SchoolMembership]:
    """Create a school and its initial active school administrator."""
    if school_repo.get_school_by_slug(db, slug=payload.slug) is not None:
        raise AppError(
            status_code=409,
            code="SCHOOL_SLUG_EXISTS",
            message="A school with this slug already exists.",
        )

    if user_repo.get_user_by_email(db, email=str(payload.initial_admin.email)) is not None:
        raise AppError(
            status_code=409,
            code="USER_EMAIL_EXISTS",
            message="A user with this email already exists.",
        )

    school = school_repo.create_school(db, name=payload.name, slug=payload.slug)
    admin_user = user_repo.create_user(
        db,
        email=str(payload.initial_admin.email),
        full_name=payload.initial_admin.full_name,
        password_hash=hash_password(payload.initial_admin.password),
        is_platform_admin=False,
        is_active=True,
    )
    db.flush()

    membership = membership_repo.create_membership(
        db,
        user_id=admin_user.id,
        school_id=school.id,
        role="school_admin",
        status="active",
    )
    db.flush()

    record_audit_event(
        db,
        action="school.created",
        target_type="school",
        target_id=school.id,
        actor_user_id=actor_user_id,
        school_id=school.id,
        metadata={
            "slug": school.slug,
            "initial_admin_user_id": str(admin_user.id),
        },
    )

    db.commit()
    db.refresh(school)
    db.refresh(admin_user)
    db.refresh(membership)
    return school, admin_user, membership


def list_schools(
    db: Session,
    *,
    status: str | None = None,
    q: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[School], int]:
    return school_repo.list_schools(
        db, status=status, q=q, offset=offset, limit=limit
    )


def update_school(
    db: Session,
    *,
    school_id: uuid.UUID,
    payload: SchoolUpdateRequest,
    actor_user_id: uuid.UUID,
) -> School:
    school = school_repo.get_school_by_id(db, school_id=school_id)
    if school is None:
        raise AppError(
            status_code=404,
            code="SCHOOL_NOT_FOUND",
            message="School not found.",
        )

    changes: dict[str, object] = {}
    if payload.name is not None:
        school.name = payload.name.strip()
        changes["name"] = school.name
    if payload.status is not None:
        school.status = payload.status
        changes["status"] = school.status
    if payload.terminology_config is not None:
        school.terminology_config = payload.terminology_config
        changes["terminology_config"] = school.terminology_config

    if changes:
        record_audit_event(
            db,
            action="school.updated",
            target_type="school",
            target_id=school.id,
            actor_user_id=actor_user_id,
            school_id=school.id,
            metadata={"changes": changes},
        )
        db.commit()
        db.refresh(school)

    return school
