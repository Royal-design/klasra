import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.grade import Grade
from app.repositories import assignment_repo, grade_repo
from app.schemas.grade import GradeUpsertRequest
from app.services.audit import record_audit_event
from app.services.lesson import _get_offering_and_check_teacher


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def upsert_submission_grade(
    db: Session,
    *,
    submission_id: uuid.UUID,
    payload: GradeUpsertRequest,
    actor_user_id: uuid.UUID,
) -> Grade:
    """ASSIGN-04: Assigned Teacher records or updates grade and feedback (audited)."""
    submission = grade_repo.get_submission_by_id(db, submission_id=submission_id)
    if submission is None or submission.assignment is None:
        raise AppError(404, "SUBMISSION_NOT_FOUND", "Submission not found.")

    assignment = submission.assignment
    _get_offering_and_check_teacher(
        db, offering_id=assignment.subject_offering_id, user_id=actor_user_id
    )

    if payload.score > assignment.max_score:
        raise AppError(
            422,
            "SCORE_EXCEEDS_MAX",
            f"Score cannot exceed the assignment max_score of {assignment.max_score}.",
        )

    now = _utcnow()
    existing = grade_repo.get_grade_by_submission_id(db, submission_id=submission.id)
    if existing is None:
        grade = Grade(
            school_id=assignment.school_id,
            submission_id=submission.id,
            assignment_id=assignment.id,
            student_user_id=submission.student_user_id,
            graded_by_user_id=actor_user_id,
            score=payload.score,
            max_score=assignment.max_score,
            letter_grade=payload.letter_grade.strip() if payload.letter_grade else None,
            feedback=payload.feedback.strip() if payload.feedback else None,
            is_published=payload.is_published,
            published_at=now if payload.is_published else None,
            graded_at=now,
        )
        db.add(grade)
        db.flush()
        record_audit_event(
            db,
            action="grade.recorded",
            target_type="grade",
            target_id=grade.id,
            actor_user_id=actor_user_id,
            school_id=assignment.school_id,
            metadata={
                "submission_id": str(submission.id),
                "student_user_id": str(submission.student_user_id),
                "score": grade.score,
                "is_published": grade.is_published,
            },
        )
    else:
        previous_score = existing.score
        previous_published = existing.is_published
        existing.graded_by_user_id = actor_user_id
        existing.score = payload.score
        existing.max_score = assignment.max_score
        existing.letter_grade = (
            payload.letter_grade.strip() if payload.letter_grade else None
        )
        existing.feedback = payload.feedback.strip() if payload.feedback else None
        existing.is_published = payload.is_published
        if payload.is_published and existing.published_at is None:
            existing.published_at = now
        existing.graded_at = now
        grade = existing

        record_audit_event(
            db,
            action="grade.updated",
            target_type="grade",
            target_id=grade.id,
            actor_user_id=actor_user_id,
            school_id=assignment.school_id,
            metadata={
                "submission_id": str(submission.id),
                "student_user_id": str(submission.student_user_id),
                "previous_score": previous_score,
                "new_score": grade.score,
                "previous_published": previous_published,
                "new_published": grade.is_published,
            },
        )

    db.commit()
    db.refresh(grade)
    return grade


def list_assignment_grades_for_teacher(
    db: Session,
    *,
    assignment_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    is_published: bool | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Grade], int]:
    assignment = assignment_repo.get_assignment_by_id(db, assignment_id=assignment_id)
    if assignment is None:
        raise AppError(404, "ASSIGNMENT_NOT_FOUND", "Assignment not found.")

    _get_offering_and_check_teacher(
        db, offering_id=assignment.subject_offering_id, user_id=actor_user_id
    )
    return grade_repo.list_grades_for_assignment(
        db,
        school_id=assignment.school_id,
        assignment_id=assignment.id,
        is_published=is_published,
        offset=offset,
        limit=limit,
    )


def list_child_grades_for_parent(
    db: Session,
    *,
    parent_user_id: uuid.UUID,
    student_user_id: uuid.UUID,
    q: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Grade], int]:
    """PROG-02: Enforce approved guardian_link before returning child's published grades."""
    link = grade_repo.get_approved_guardian_link_for_child(
        db, parent_user_id=parent_user_id, student_user_id=student_user_id
    )
    if link is None:
        raise AppError(
            403,
            "FORBIDDEN",
            "You do not have an approved guardian link for this student.",
        )

    return grade_repo.list_published_grades_for_student(
        db,
        student_user_id=student_user_id,
        school_id=link.school_id,
        q=q,
        offset=offset,
        limit=limit,
    )
