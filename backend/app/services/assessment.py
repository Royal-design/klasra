import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.assessment import (
    Assessment,
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentQuestion,
)
from app.repositories import assessment_repo, grade_repo
from app.schemas.assessment import (
    AssessmentCreateRequest,
    AssessmentQuestionCreateRequest,
    AssessmentUpdateRequest,
    GradeAttemptRequest,
    SubmitAttemptRequest,
)
from app.services.audit import record_audit_event
from app.services.lesson import (
    _check_offering_read_access,
    _get_offering_and_check_teacher,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def create_assessment(
    db: Session,
    *,
    offering_id: uuid.UUID,
    payload: AssessmentCreateRequest,
    actor_user_id: uuid.UUID,
) -> Assessment:
    offering = _get_offering_and_check_teacher(
        db, offering_id=offering_id, user_id=actor_user_id
    )
    now = _utcnow()
    assessment = Assessment(
        school_id=offering.school_id,
        subject_offering_id=offering.id,
        created_by_user_id=actor_user_id,
        title=payload.title,
        instructions=payload.instructions,
        assessment_type=payload.assessment_type,
        status=payload.status,
        available_from=_as_utc(payload.available_from),
        available_until=_as_utc(payload.available_until),
        time_limit_minutes=payload.time_limit_minutes,
        max_attempts=payload.max_attempts,
        shuffle_questions=payload.shuffle_questions,
        shuffle_options=payload.shuffle_options,
        show_results_immediately=payload.show_results_immediately,
        total_points=0.0,
        published_at=now if payload.status == "published" else None,
    )
    db.add(assessment)
    db.flush()

    record_audit_event(
        db,
        action="assessment.created",
        target_type="assessment",
        target_id=assessment.id,
        actor_user_id=actor_user_id,
        school_id=offering.school_id,
        metadata={
            "subject_offering_id": str(offering.id),
            "assessment_type": assessment.assessment_type,
            "status": assessment.status,
        },
    )
    db.commit()
    db.refresh(assessment)
    return assessment


def list_assessments(
    db: Session,
    *,
    offering_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    assessment_type: str | None = None,
    status: str | None = None,
    q: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Assessment], int, bool]:
    offering, is_teacher = _check_offering_read_access(
        db, offering_id=offering_id, user_id=actor_user_id
    )
    items, total = assessment_repo.list_assessments_for_offering(
        db,
        school_id=offering.school_id,
        offering_id=offering.id,
        published_only=not is_teacher,
        assessment_type=assessment_type.strip().lower() if assessment_type else None,
        status=status.strip().lower() if (is_teacher and status) else None,
        q=q,
        offset=offset,
        limit=limit,
    )
    return items, total, is_teacher


def update_assessment(
    db: Session,
    *,
    offering_id: uuid.UUID,
    assessment_id: uuid.UUID,
    payload: AssessmentUpdateRequest,
    actor_user_id: uuid.UUID,
) -> Assessment:
    offering = _get_offering_and_check_teacher(
        db, offering_id=offering_id, user_id=actor_user_id
    )
    assessment = assessment_repo.get_assessment_for_offering(
        db,
        school_id=offering.school_id,
        offering_id=offering.id,
        assessment_id=assessment_id,
    )
    if assessment is None:
        raise AppError(404, "ASSESSMENT_NOT_FOUND", "Assessment not found.")

    if payload.title is not None:
        assessment.title = payload.title
    if "instructions" in payload.model_fields_set:
        assessment.instructions = payload.instructions
    if payload.assessment_type is not None:
        assessment.assessment_type = payload.assessment_type
    if "available_from" in payload.model_fields_set:
        assessment.available_from = _as_utc(payload.available_from)
    if "available_until" in payload.model_fields_set:
        assessment.available_until = _as_utc(payload.available_until)
    if "time_limit_minutes" in payload.model_fields_set:
        assessment.time_limit_minutes = payload.time_limit_minutes
    if payload.max_attempts is not None:
        assessment.max_attempts = payload.max_attempts
    if payload.shuffle_questions is not None:
        assessment.shuffle_questions = payload.shuffle_questions
    if payload.shuffle_options is not None:
        assessment.shuffle_options = payload.shuffle_options
    if payload.show_results_immediately is not None:
        assessment.show_results_immediately = payload.show_results_immediately
    if payload.status is not None:
        assessment.status = payload.status
        if payload.status == "published" and assessment.published_at is None:
            assessment.published_at = _utcnow()

    record_audit_event(
        db,
        action="assessment.updated",
        target_type="assessment",
        target_id=assessment.id,
        actor_user_id=actor_user_id,
        school_id=offering.school_id,
        metadata={"status": assessment.status, "assessment_type": assessment.assessment_type},
    )
    db.commit()
    db.refresh(assessment)
    return assessment


def add_question_to_assessment(
    db: Session,
    *,
    offering_id: uuid.UUID,
    assessment_id: uuid.UUID,
    payload: AssessmentQuestionCreateRequest,
    actor_user_id: uuid.UUID,
) -> AssessmentQuestion:
    offering = _get_offering_and_check_teacher(
        db, offering_id=offering_id, user_id=actor_user_id
    )
    assessment = assessment_repo.get_assessment_for_offering(
        db,
        school_id=offering.school_id,
        offering_id=offering.id,
        assessment_id=assessment_id,
    )
    if assessment is None:
        raise AppError(404, "ASSESSMENT_NOT_FOUND", "Assessment not found.")

    question = AssessmentQuestion(
        school_id=offering.school_id,
        assessment_id=assessment.id,
        question_type=payload.question_type,
        prompt=payload.prompt.strip(),
        options=[opt.model_dump() for opt in payload.options] if payload.options else None,
        correct_answers=payload.correct_answers,
        points=payload.points,
        display_order=payload.display_order,
    )
    db.add(question)
    db.flush()

    assessment.total_points = assessment_repo.recalculate_total_points(
        db, school_id=offering.school_id, assessment_id=assessment.id
    )
    db.commit()
    db.refresh(question)
    return question


def delete_question_from_assessment(
    db: Session,
    *,
    offering_id: uuid.UUID,
    assessment_id: uuid.UUID,
    question_id: uuid.UUID,
    actor_user_id: uuid.UUID,
) -> None:
    offering = _get_offering_and_check_teacher(
        db, offering_id=offering_id, user_id=actor_user_id
    )
    assessment = assessment_repo.get_assessment_for_offering(
        db,
        school_id=offering.school_id,
        offering_id=offering.id,
        assessment_id=assessment_id,
    )
    if assessment is None:
        raise AppError(404, "ASSESSMENT_NOT_FOUND", "Assessment not found.")

    question = assessment_repo.get_question_for_assessment(
        db,
        school_id=offering.school_id,
        assessment_id=assessment.id,
        question_id=question_id,
    )
    if question is None:
        raise AppError(404, "QUESTION_NOT_FOUND", "Question not found.")

    db.delete(question)
    db.flush()
    assessment.total_points = assessment_repo.recalculate_total_points(
        db, school_id=offering.school_id, assessment_id=assessment.id
    )
    db.commit()


def start_attempt(
    db: Session,
    *,
    assessment_id: uuid.UUID,
    actor_user_id: uuid.UUID,
) -> AssessmentAttempt:
    assessment = assessment_repo.get_assessment_by_id(db, assessment_id=assessment_id)
    if assessment is None:
        raise AppError(404, "ASSESSMENT_NOT_FOUND", "Assessment not found.")

    _offering, is_teacher = _check_offering_read_access(
        db, offering_id=assessment.subject_offering_id, user_id=actor_user_id
    )
    if is_teacher:
        raise AppError(403, "FORBIDDEN", "Only enrolled students can start an assessment attempt.")
    if assessment.status != "published":
        raise AppError(409, "ASSESSMENT_NOT_OPEN", "This assessment is not currently open.")

    now = _utcnow()
    avail_from = _as_utc(assessment.available_from)
    avail_until = _as_utc(assessment.available_until)
    if avail_from is not None and now < avail_from:
        raise AppError(409, "ASSESSMENT_NOT_OPEN_YET", "This assessment has not opened yet.")
    if avail_until is not None and now > avail_until:
        raise AppError(409, "ASSESSMENT_CLOSED", "The window for this assessment has closed.")

    existing = assessment_repo.get_in_progress_attempt(
        db,
        school_id=assessment.school_id,
        assessment_id=assessment.id,
        student_user_id=actor_user_id,
    )
    if existing is not None:
        return existing

    attempt_count = assessment_repo.count_student_attempts(
        db,
        school_id=assessment.school_id,
        assessment_id=assessment.id,
        student_user_id=actor_user_id,
    )
    if attempt_count >= assessment.max_attempts:
        raise AppError(
            409,
            "MAX_ATTEMPTS_REACHED",
            "You have reached the maximum number of attempts for this assessment.",
        )

    deadline: datetime | None = avail_until
    if assessment.time_limit_minutes is not None:
        timed_deadline = now + timedelta(minutes=assessment.time_limit_minutes)
        deadline = min(timed_deadline, avail_until) if avail_until is not None else timed_deadline

    attempt = AssessmentAttempt(
        school_id=assessment.school_id,
        assessment_id=assessment.id,
        student_user_id=actor_user_id,
        attempt_number=attempt_count + 1,
        status="in_progress",
        started_at=now,
        deadline_at=deadline,
        max_score=assessment.total_points,
        is_published=False,
    )
    db.add(attempt)
    db.flush()
    record_audit_event(
        db,
        action="assessment_attempt.started",
        target_type="assessment_attempt",
        target_id=attempt.id,
        actor_user_id=actor_user_id,
        school_id=assessment.school_id,
        metadata={
            "assessment_id": str(assessment.id),
            "attempt_number": attempt.attempt_number,
        },
    )
    db.commit()
    db.refresh(attempt)
    return attempt


def submit_attempt(
    db: Session,
    *,
    attempt_id: uuid.UUID,
    payload: SubmitAttemptRequest,
    actor_user_id: uuid.UUID,
) -> AssessmentAttempt:
    attempt = assessment_repo.get_attempt_by_id(db, attempt_id=attempt_id)
    if attempt is None:
        raise AppError(404, "ATTEMPT_NOT_FOUND", "Assessment attempt not found.")
    if attempt.student_user_id != actor_user_id:
        raise AppError(403, "FORBIDDEN", "You can only submit your own assessment attempt.")
    if attempt.status != "in_progress":
        raise AppError(409, "ATTEMPT_ALREADY_SUBMITTED", "This attempt has already been submitted.")

    now = _utcnow()
    deadline = _as_utc(attempt.deadline_at)
    # Allow a 30-second network grace window past the timer deadline
    if deadline is not None and now > deadline + timedelta(seconds=30):
        raise AppError(409, "ATTEMPT_EXPIRED", "The time limit for this attempt has expired.")

    assessment = attempt.assessment
    question_map = {q.id: q for q in (assessment.questions or [])}
    has_manual_questions = any(q.question_type == "short_answer" for q in question_map.values())

    auto_score = 0.0
    for item in payload.answers:
        question = question_map.get(item.question_id)
        if question is None:
            continue

        selected_norm: list[str] | None = None
        is_correct: bool | None = None
        points_awarded = 0.0

        if question.question_type in {"single_choice", "true_false", "multi_select"}:
            selected_norm = sorted(
                {opt.strip().upper() for opt in (item.selected_options or []) if opt.strip()}
            )
            expected = sorted(question.correct_answers or [])
            is_correct = selected_norm == expected
            if is_correct:
                points_awarded = float(question.points)
                auto_score += points_awarded

        ans = assessment_repo.get_answer_for_attempt_question(
            db, attempt_id=attempt.id, question_id=question.id
        )
        if ans is None:
            ans = AssessmentAnswer(
                school_id=attempt.school_id,
                attempt_id=attempt.id,
                question_id=question.id,
            )
            db.add(ans)
        ans.selected_options = selected_norm
        ans.text_answer = item.text_answer.strip() if item.text_answer else None
        ans.is_correct = is_correct
        ans.points_awarded = points_awarded

    attempt.submitted_at = now
    attempt.auto_score = auto_score
    attempt.manual_score = 0.0
    attempt.total_score = auto_score
    attempt.max_score = float(assessment.total_points)

    if not has_manual_questions:
        attempt.status = "graded"
        if assessment.show_results_immediately:
            attempt.is_published = True
            attempt.published_at = now
    else:
        attempt.status = "submitted"

    record_audit_event(
        db,
        action="assessment_attempt.submitted",
        target_type="assessment_attempt",
        target_id=attempt.id,
        actor_user_id=actor_user_id,
        school_id=attempt.school_id,
        metadata={
            "assessment_id": str(assessment.id),
            "auto_score": attempt.auto_score,
            "is_published": attempt.is_published,
        },
    )
    db.commit()
    db.refresh(attempt)
    return attempt


def list_attempts_for_assessment(
    db: Session,
    *,
    assessment_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    student_user_id: uuid.UUID | None = None,
    status: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[AssessmentAttempt], int, bool]:
    assessment = assessment_repo.get_assessment_by_id(db, assessment_id=assessment_id)
    if assessment is None:
        raise AppError(404, "ASSESSMENT_NOT_FOUND", "Assessment not found.")

    _offering, is_teacher = _check_offering_read_access(
        db, offering_id=assessment.subject_offering_id, user_id=actor_user_id
    )
    effective_student = student_user_id if is_teacher else actor_user_id
    items, total = assessment_repo.list_attempts_for_assessment(
        db,
        school_id=assessment.school_id,
        assessment_id=assessment.id,
        student_user_id=effective_student,
        status=status.strip().lower() if status else None,
        offset=offset,
        limit=limit,
    )
    return items, total, is_teacher


def grade_attempt(
    db: Session,
    *,
    attempt_id: uuid.UUID,
    payload: GradeAttemptRequest,
    actor_user_id: uuid.UUID,
) -> AssessmentAttempt:
    attempt = assessment_repo.get_attempt_by_id(db, attempt_id=attempt_id)
    if attempt is None:
        raise AppError(404, "ATTEMPT_NOT_FOUND", "Assessment attempt not found.")

    _get_offering_and_check_teacher(
        db, offering_id=attempt.assessment.subject_offering_id, user_id=actor_user_id
    )
    if attempt.status == "in_progress":
        raise AppError(409, "ATTEMPT_IN_PROGRESS", "Cannot grade an attempt that has not been submitted.")

    question_map = {q.id: q for q in (attempt.assessment.questions or [])}
    for grade_item in payload.answer_grades:
        question = question_map.get(grade_item.question_id)
        if question is None:
            raise AppError(422, "INVALID_QUESTION", "Question does not belong to this assessment.")
        if grade_item.points_awarded > float(question.points):
            raise AppError(
                422,
                "SCORE_EXCEEDS_MAX",
                f"Awarded points cannot exceed question maximum ({question.points}).",
            )
        ans = assessment_repo.get_answer_for_attempt_question(
            db, attempt_id=attempt.id, question_id=question.id
        )
        if ans is None:
            ans = AssessmentAnswer(
                school_id=attempt.school_id,
                attempt_id=attempt.id,
                question_id=question.id,
            )
            db.add(ans)
        ans.points_awarded = grade_item.points_awarded
        ans.feedback = grade_item.feedback.strip() if grade_item.feedback else None

    db.flush()
    db.refresh(attempt)

    auto_total = 0.0
    manual_total = 0.0
    for ans in attempt.answers:
        q = question_map.get(ans.question_id)
        if q and q.question_type == "short_answer":
            manual_total += float(ans.points_awarded)
        else:
            auto_total += float(ans.points_awarded)

    attempt.auto_score = auto_total
    attempt.manual_score = manual_total
    attempt.total_score = auto_total + manual_total
    attempt.teacher_feedback = (
        payload.teacher_feedback.strip() if payload.teacher_feedback else None
    )
    attempt.status = "graded"
    attempt.graded_by_user_id = actor_user_id
    attempt.is_published = payload.is_published
    if payload.is_published and attempt.published_at is None:
        attempt.published_at = _utcnow()

    record_audit_event(
        db,
        action="assessment_attempt.graded",
        target_type="assessment_attempt",
        target_id=attempt.id,
        actor_user_id=actor_user_id,
        school_id=attempt.school_id,
        metadata={
            "assessment_id": str(attempt.assessment_id),
            "student_user_id": str(attempt.student_user_id),
            "total_score": attempt.total_score,
            "is_published": attempt.is_published,
        },
    )
    db.commit()
    db.refresh(attempt)
    return attempt


def list_my_published_assessment_results(
    db: Session,
    *,
    student_user_id: uuid.UUID,
    assessment_type: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[AssessmentAttempt], int]:
    return assessment_repo.list_published_attempts_for_student(
        db,
        student_user_id=student_user_id,
        assessment_type=assessment_type.strip().lower() if assessment_type else None,
        offset=offset,
        limit=limit,
    )


def list_child_published_assessment_results(
    db: Session,
    *,
    parent_user_id: uuid.UUID,
    student_user_id: uuid.UUID,
    assessment_type: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[AssessmentAttempt], int]:
    link = grade_repo.get_approved_guardian_link_for_child(
        db, parent_user_id=parent_user_id, student_user_id=student_user_id
    )
    if link is None:
        raise AppError(
            403,
            "FORBIDDEN",
            "You do not have an approved guardian link to view this student's assessment results.",
        )
    return assessment_repo.list_published_attempts_for_student(
        db,
        student_user_id=student_user_id,
        school_id=link.school_id,
        assessment_type=assessment_type.strip().lower() if assessment_type else None,
        offset=offset,
        limit=limit,
    )
