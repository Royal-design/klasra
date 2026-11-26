import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_current_auth, verify_csrf
from app.db.session import get_db
from app.repositories import attendance_repo
from app.schemas.attendance import (
    AttendanceBatchUpsertRequest,
    AttendanceRecordResponse,
)
from app.schemas.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
    get_pagination_params,
)
from app.services import attendance as attendance_service

router = APIRouter(tags=["attendance"])


def _to_response(rec) -> AttendanceRecordResponse:
    subject_name = None
    subject_code = None
    class_group_name = None
    if rec.subject_offering is not None:
        if rec.subject_offering.subject is not None:
            subject_name = rec.subject_offering.subject.name
            subject_code = rec.subject_offering.subject.code
        if rec.subject_offering.class_group is not None:
            class_group_name = rec.subject_offering.class_group.name

    return AttendanceRecordResponse(
        id=rec.id,
        school_id=rec.school_id,
        school_name=rec.school.name if rec.school else None,
        subject_offering_id=rec.subject_offering_id,
        subject_name=subject_name,
        subject_code=subject_code,
        class_group_name=class_group_name,
        student_user_id=rec.student_user_id,
        student_full_name=rec.student.full_name if rec.student else None,
        attendance_date=rec.attendance_date,
        status=rec.status,
        notes=rec.notes,
        recorded_by_user_id=rec.recorded_by_user_id,
        recorded_by_full_name=rec.recorded_by.full_name if rec.recorded_by else None,
        updated_by_user_id=rec.updated_by_user_id,
        updated_by_full_name=rec.updated_by.full_name if rec.updated_by else None,
        recorded_at=rec.recorded_at,
        updated_at=rec.updated_at,
    )


@router.put(
    "/offerings/{offering_id}/attendance",
    response_model=list[AttendanceRecordResponse],
    summary="Record or update class attendance for a date (Assigned Teacher — ATT-01, ATT-02)",
)
def record_attendance_endpoint(
    offering_id: uuid.UUID,
    payload: AttendanceBatchUpsertRequest,
    auth: AuthContext = Depends(verify_csrf),
    db: Session = Depends(get_db),
) -> list[AttendanceRecordResponse]:
    records = attendance_service.record_offering_attendance(
        db,
        offering_id=offering_id,
        payload=payload,
        actor_user_id=auth.user.id,
    )
    return [_to_response(r) for r in records]


@router.get(
    "/offerings/{offering_id}/attendance",
    response_model=PaginatedResponse[AttendanceRecordResponse],
    summary="List attendance records for a subject offering (Assigned Teacher or School Admin)",
)
def list_offering_attendance_endpoint(
    offering_id: uuid.UUID,
    attendance_date: date | None = Query(default=None),
    student_user_id: uuid.UUID | None = Query(default=None),
    attendance_status: str | None = Query(default=None, alias="status"),
    pagination: PaginationParams = Depends(get_pagination_params),
    auth: AuthContext = Depends(get_current_auth),
    db: Session = Depends(get_db),
) -> PaginatedResponse[AttendanceRecordResponse]:
    items, total = attendance_service.list_offering_attendance(
        db,
        offering_id=offering_id,
        actor_user_id=auth.user.id,
        attendance_date=attendance_date,
        student_user_id=student_user_id,
        status=attendance_status,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [_to_response(r) for r in items], total=total, pagination=pagination
    )


@router.get(
    "/students/me/attendance",
    response_model=PaginatedResponse[AttendanceRecordResponse],
    summary="View own attendance history (Student — PROG-01)",
)
def list_my_attendance_endpoint(
    subject_offering_id: uuid.UUID | None = Query(default=None),
    attendance_status: str | None = Query(default=None, alias="status"),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    pagination: PaginationParams = Depends(get_pagination_params),
    auth: AuthContext = Depends(get_current_auth),
    db: Session = Depends(get_db),
) -> PaginatedResponse[AttendanceRecordResponse]:
    items, total = attendance_repo.list_for_student(
        db,
        student_user_id=auth.user.id,
        subject_offering_id=subject_offering_id,
        status=attendance_status,
        date_from=date_from,
        date_to=date_to,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [_to_response(r) for r in items], total=total, pagination=pagination
    )


@router.get(
    "/parent/children/{student_id}/attendance",
    response_model=PaginatedResponse[AttendanceRecordResponse],
    summary="View approved linked child's attendance history (Parent — PROG-02)",
)
def list_child_attendance_endpoint(
    student_id: uuid.UUID,
    attendance_status: str | None = Query(default=None, alias="status"),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    pagination: PaginationParams = Depends(get_pagination_params),
    auth: AuthContext = Depends(get_current_auth),
    db: Session = Depends(get_db),
) -> PaginatedResponse[AttendanceRecordResponse]:
    items, total = attendance_service.list_child_attendance_for_parent(
        db,
        parent_user_id=auth.user.id,
        student_user_id=student_id,
        status=attendance_status,
        date_from=date_from,
        date_to=date_to,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [_to_response(r) for r in items], total=total, pagination=pagination
    )
