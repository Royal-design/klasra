import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_current_auth, verify_csrf
from app.db.session import get_db
from app.schemas.assessment import (
    AssessmentAnswerResponse,
    AssessmentAttemptResponse,
    AssessmentCreateRequest,
    AssessmentQuestionCreateRequest,
    AssessmentQuestionResponse,
    AssessmentResponse,
    AssessmentUpdateRequest,
    GradeAttemptRequest,
    SubmitAttemptRequest,
)
from app.schemas.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
    get_pagination_params,
)
from app.services import assessment as assessment_service

router = APIRouter(tags=["assessments-quizzes-exams"])


def _to_question_response(q, *, include_answers: bool) -> AssessmentQuestionResponse:
    return AssessmentQuestionResponse(
        id=q.id,
        question_type=q.question_type,
        prompt=q.prompt,
        options=q.options,
        correct_answers=q.correct_answers if include_answers else None,
        points=q.points,
        display_order=q.display_order,
    )


def _to_assessment_response(a, *, include_answers: bool) -> AssessmentResponse:
    questions = a.questions or []
    return AssessmentResponse(
        id=a.id,
        school_id=a.school_id,
        subject_offering_id=a.subject_offering_id,
        created_by_user_id=a.created_by_user_id,
        author_full_name=a.author.full_name if a.author else None,
        title=a.title,
        instructions=a.instructions,
        assessment_type=a.assessment_type,
        status=a.status,
        available_from=a.available_from,
        available_until=a.available_until,
        time_limit_minutes=a.time_limit_minutes,
        max_attempts=a.max_attempts,
        shuffle_questions=a.shuffle_questions,
        shuffle_options=a.shuffle_options,
        show_results_immediately=a.show_results_immediately,
        total_points=a.total_points,
        question_count=len(questions),
        questions=[_to_question_response(q, include_answers=include_answers) for q in questions],
        published_at=a.published_at,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


def _to_attempt_response(attempt, *, reveal_scores: bool) -> AssessmentAttemptResponse:
    offering = attempt.assessment.subject_offering if attempt.assessment else None
    subject = offering.subject if offering else None
    show = reveal_scores or attempt.is_published
    return AssessmentAttemptResponse(
        id=attempt.id,
        school_id=attempt.school_id,
        school_name=attempt.school.name if attempt.school else None,
        assessment_id=attempt.assessment_id,
        assessment_title=attempt.assessment.title if attempt.assessment else None,
        assessment_type=attempt.assessment.assessment_type if attempt.assessment else None,
        subject_name=subject.name if subject else None,
        subject_code=subject.code if subject else None,
        student_user_id=attempt.student_user_id,
        student_full_name=attempt.student.full_name if attempt.student else None,
        attempt_number=attempt.attempt_number,
        status=attempt.status,
        started_at=attempt.started_at,
        deadline_at=attempt.deadline_at,
        submitted_at=attempt.submitted_at,
        auto_score=attempt.auto_score if show else None,
        manual_score=attempt.manual_score if show else None,
        total_score=attempt.total_score if show else None,
        max_score=attempt.max_score,
        teacher_feedback=attempt.teacher_feedback if show else None,
        is_published=attempt.is_published,
        published_at=attempt.published_at,
        answers=[
            AssessmentAnswerResponse(
                id=ans.id,
                question_id=ans.question_id,
                selected_options=ans.selected_options,
                text_answer=ans.text_answer,
                is_correct=ans.is_correct if show else None,
                points_awarded=ans.points_awarded if show else 0.0,
                feedback=ans.feedback if show else None,
            )
            for ans in (attempt.answers or [])
        ],
        created_at=attempt.created_at,
        updated_at=attempt.updated_at,
    )


@router.post(
    "/offerings/{offering_id}/assessments",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a quiz, test (CA), or exam for an assigned subject offering (Assigned Teacher)",
)
def create_assessment_endpoint(
    offering_id: uuid.UUID,
    payload: AssessmentCreateRequest,
    auth: AuthContext = Depends(verify_csrf),
    db: Session = Depends(get_db),
) -> AssessmentResponse:
    assessment = assessment_service.create_assessment(
        db,
        offering_id=offering_id,
        payload=payload,
        actor_user_id=auth.user.id,
    )
    return _to_assessment_response(assessment, include_answers=True)


@router.get(
    "/offerings/{offering_id}/assessments",
    response_model=PaginatedResponse[AssessmentResponse],
    summary="List quizzes, tests, and exams for an offering (Assigned Teacher or Enrolled Student)",
)
def list_assessments_endpoint(
    offering_id: uuid.UUID,
    assessment_type: str | None = Query(default=None),
    assessment_status: str | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None, max_length=100),
    pagination: PaginationParams = Depends(get_pagination_params),
    auth: AuthContext = Depends(get_current_auth),
    db: Session = Depends(get_db),
) -> PaginatedResponse[AssessmentResponse]:
    items, total, is_teacher = assessment_service.list_assessments(
        db,
        offering_id=offering_id,
        actor_user_id=auth.user.id,
        assessment_type=assessment_type,
        status=assessment_status,
        q=q,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [_to_assessment_response(a, include_answers=is_teacher) for a in items],
        total=total,
        pagination=pagination,
    )


@router.patch(
    "/offerings/{offering_id}/assessments/{assessment_id}",
    response_model=AssessmentResponse,
    summary="Update or publish/close a quiz, test, or exam (Assigned Teacher)",
)
def update_assessment_endpoint(
    offering_id: uuid.UUID,
    assessment_id: uuid.UUID,
    payload: AssessmentUpdateRequest,
    auth: AuthContext = Depends(verify_csrf),
    db: Session = Depends(get_db),
) -> AssessmentResponse:
    assessment = assessment_service.update_assessment(
        db,
        offering_id=offering_id,
        assessment_id=assessment_id,
        payload=payload,
        actor_user_id=auth.user.id,
    )
    return _to_assessment_response(assessment, include_answers=True)


@router.post(
    "/offerings/{offering_id}/assessments/{assessment_id}/questions",
    response_model=AssessmentQuestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a question to an assessment (Assigned Teacher)",
)
def add_question_endpoint(
    offering_id: uuid.UUID,
    assessment_id: uuid.UUID,
    payload: AssessmentQuestionCreateRequest,
    auth: AuthContext = Depends(verify_csrf),
    db: Session = Depends(get_db),
) -> AssessmentQuestionResponse:
    question = assessment_service.add_question_to_assessment(
        db,
        offering_id=offering_id,
        assessment_id=assessment_id,
        payload=payload,
        actor_user_id=auth.user.id,
    )
    return _to_question_response(question, include_answers=True)


@router.delete(
    "/offerings/{offering_id}/assessments/{assessment_id}/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a question from an assessment (Assigned Teacher)",
)
def delete_question_endpoint(
    offering_id: uuid.UUID,
    assessment_id: uuid.UUID,
    question_id: uuid.UUID,
    auth: AuthContext = Depends(verify_csrf),
    db: Session = Depends(get_db),
) -> Response:
    assessment_service.delete_question_from_assessment(
        db,
        offering_id=offering_id,
        assessment_id=assessment_id,
        question_id=question_id,
        actor_user_id=auth.user.id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/assessments/{assessment_id}/attempts",
    response_model=AssessmentAttemptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start or resume a timed assessment attempt (Enrolled Student)",
)
def start_attempt_endpoint(
    assessment_id: uuid.UUID,
    auth: AuthContext = Depends(verify_csrf),
    db: Session = Depends(get_db),
) -> AssessmentAttemptResponse:
    attempt = assessment_service.start_attempt(
        db, assessment_id=assessment_id, actor_user_id=auth.user.id
    )
    return _to_attempt_response(attempt, reveal_scores=False)


@router.post(
    "/attempts/{attempt_id}/submit",
    response_model=AssessmentAttemptResponse,
    summary="Submit answers for an active attempt with instant objective auto-grading (Student)",
)
def submit_attempt_endpoint(
    attempt_id: uuid.UUID,
    payload: SubmitAttemptRequest,
    auth: AuthContext = Depends(verify_csrf),
    db: Session = Depends(get_db),
) -> AssessmentAttemptResponse:
    attempt = assessment_service.submit_attempt(
        db,
        attempt_id=attempt_id,
        payload=payload,
        actor_user_id=auth.user.id,
    )
    return _to_attempt_response(attempt, reveal_scores=False)


@router.get(
    "/assessments/{assessment_id}/attempts",
    response_model=PaginatedResponse[AssessmentAttemptResponse],
    summary="List assessment attempts (Teacher sees all; Student sees own only)",
)
def list_attempts_endpoint(
    assessment_id: uuid.UUID,
    student_user_id: uuid.UUID | None = Query(default=None),
    attempt_status: str | None = Query(default=None, alias="status"),
    pagination: PaginationParams = Depends(get_pagination_params),
    auth: AuthContext = Depends(get_current_auth),
    db: Session = Depends(get_db),
) -> PaginatedResponse[AssessmentAttemptResponse]:
    items, total, is_teacher = assessment_service.list_attempts_for_assessment(
        db,
        assessment_id=assessment_id,
        actor_user_id=auth.user.id,
        student_user_id=student_user_id,
        status=attempt_status,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [_to_attempt_response(a, reveal_scores=is_teacher) for a in items],
        total=total,
        pagination=pagination,
    )


@router.put(
    "/attempts/{attempt_id}/grade",
    response_model=AssessmentAttemptResponse,
    summary="Grade short-answer questions and publish/unpublish attempt result (Assigned Teacher)",
)
def grade_attempt_endpoint(
    attempt_id: uuid.UUID,
    payload: GradeAttemptRequest,
    auth: AuthContext = Depends(verify_csrf),
    db: Session = Depends(get_db),
) -> AssessmentAttemptResponse:
    attempt = assessment_service.grade_attempt(
        db,
        attempt_id=attempt_id,
        payload=payload,
        actor_user_id=auth.user.id,
    )
    return _to_attempt_response(attempt, reveal_scores=True)


@router.get(
    "/students/me/assessments",
    response_model=PaginatedResponse[AssessmentAttemptResponse],
    summary="View own published quiz, test, and exam results (Student — PROG-01)",
)
def list_my_assessment_results_endpoint(
    assessment_type: str | None = Query(default=None),
    pagination: PaginationParams = Depends(get_pagination_params),
    auth: AuthContext = Depends(get_current_auth),
    db: Session = Depends(get_db),
) -> PaginatedResponse[AssessmentAttemptResponse]:
    items, total = assessment_service.list_my_published_assessment_results(
        db,
        student_user_id=auth.user.id,
        assessment_type=assessment_type,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [_to_attempt_response(a, reveal_scores=True) for a in items],
        total=total,
        pagination=pagination,
    )


@router.get(
    "/parent/children/{student_id}/assessments",
    response_model=PaginatedResponse[AssessmentAttemptResponse],
    summary="View an approved linked child's published quiz, test, and exam results (Parent — PROG-02)",
)
def list_child_assessment_results_endpoint(
    student_id: uuid.UUID,
    assessment_type: str | None = Query(default=None),
    pagination: PaginationParams = Depends(get_pagination_params),
    auth: AuthContext = Depends(get_current_auth),
    db: Session = Depends(get_db),
) -> PaginatedResponse[AssessmentAttemptResponse]:
    items, total = assessment_service.list_child_published_assessment_results(
        db,
        parent_user_id=auth.user.id,
        student_user_id=student_id,
        assessment_type=assessment_type,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [_to_attempt_response(a, reveal_scores=True) for a in items],
        total=total,
        pagination=pagination,
    )
