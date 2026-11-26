import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_current_auth, verify_csrf
from app.db.session import get_db
from app.repositories import grade_repo
from app.schemas.grade import GradeResponse, GradeUpsertRequest
from app.schemas.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
    get_pagination_params,
)
from app.services import grade as grade_service

router = APIRouter(tags=["grades-and-progress"])


def _to_grade_response(grade) -> GradeResponse:
    subject_name = None
    subject_code = None
    class_group_name = None
    if grade.assignment is not None and grade.assignment.subject_offering is not None:
        offering = grade.assignment.subject_offering
        if offering.subject is not None:
            subject_name = offering.subject.name
            subject_code = offering.subject.code
        if offering.class_group is not None:
            class_group_name = offering.class_group.name

    return GradeResponse(
        id=grade.id,
        school_id=grade.school_id,
        school_name=grade.school.name if grade.school else None,
        submission_id=grade.submission_id,
        assignment_id=grade.assignment_id,
        assignment_title=grade.assignment.title if grade.assignment else None,
        subject_name=subject_name,
        subject_code=subject_code,
        class_group_name=class_group_name,
        student_user_id=grade.student_user_id,
        student_full_name=grade.student.full_name if grade.student else None,
        graded_by_user_id=grade.graded_by_user_id,
        graded_by_full_name=grade.grader.full_name if grade.grader else None,
        score=grade.score,
        max_score=grade.max_score,
        letter_grade=grade.letter_grade,
        feedback=grade.feedback,
        is_published=grade.is_published,
        published_at=grade.published_at,
        graded_at=grade.graded_at,
        created_at=grade.created_at,
        updated_at=grade.updated_at,
    )


@router.put(
    "/submissions/{submission_id}/grade",
    response_model=GradeResponse,
    summary="Record or update grade and feedback for a submission (Assigned Teacher)",
)
def upsert_grade_endpoint(
    submission_id: uuid.UUID,
    payload: GradeUpsertRequest,
    auth: AuthContext = Depends(verify_csrf),
    db: Session = Depends(get_db),
) -> GradeResponse:
    grade = grade_service.upsert_submission_grade(
        db,
        submission_id=submission_id,
        payload=payload,
        actor_user_id=auth.user.id,
    )
    return _to_grade_response(grade)


@router.get(
    "/assignments/{assignment_id}/grades",
    response_model=PaginatedResponse[GradeResponse],
    summary="List all grades (draft and published) for an assignment (Assigned Teacher)",
)
def list_assignment_grades_endpoint(
    assignment_id: uuid.UUID,
    is_published: bool | None = Query(default=None),
    pagination: PaginationParams = Depends(get_pagination_params),
    auth: AuthContext = Depends(get_current_auth),
    db: Session = Depends(get_db),
) -> PaginatedResponse[GradeResponse]:
    items, total = grade_service.list_assignment_grades_for_teacher(
        db,
        assignment_id=assignment_id,
        actor_user_id=auth.user.id,
        is_published=is_published,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [_to_grade_response(g) for g in items], total=total, pagination=pagination
    )


@router.get(
    "/students/me/grades",
    response_model=PaginatedResponse[GradeResponse],
    summary="View own published grades and teacher feedback (Student — PROG-01)",
)
def list_my_grades_endpoint(
    subject_offering_id: uuid.UUID | None = Query(default=None),
    q: str | None = Query(default=None, max_length=100),
    pagination: PaginationParams = Depends(get_pagination_params),
    auth: AuthContext = Depends(get_current_auth),
    db: Session = Depends(get_db),
) -> PaginatedResponse[GradeResponse]:
    items, total = grade_repo.list_published_grades_for_student(
        db,
        student_user_id=auth.user.id,
        subject_offering_id=subject_offering_id,
        q=q,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [_to_grade_response(g) for g in items], total=total, pagination=pagination
    )


@router.get(
    "/parent/children/{student_id}/grades",
    response_model=PaginatedResponse[GradeResponse],
    summary="View approved linked child's published grades and feedback (Parent — PROG-02)",
)
def list_child_grades_endpoint(
    student_id: uuid.UUID,
    q: str | None = Query(default=None, max_length=100),
    pagination: PaginationParams = Depends(get_pagination_params),
    auth: AuthContext = Depends(get_current_auth),
    db: Session = Depends(get_db),
) -> PaginatedResponse[GradeResponse]:
    items, total = grade_service.list_child_grades_for_parent(
        db,
        parent_user_id=auth.user.id,
        student_user_id=student_id,
        q=q,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [_to_grade_response(g) for g in items], total=total, pagination=pagination
    )
