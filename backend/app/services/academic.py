import uuid

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.academic import (
    AcademicYear,
    ClassGroup,
    Enrollment,
    OfferingTeacher,
    Subject,
    SubjectOffering,
    Term,
    YearLevel,
)
from app.repositories import academic_repo, membership_repo
from app.schemas.academic import (
    AcademicYearCreateRequest,
    AcademicYearUpdateRequest,
    ClassGroupCreateRequest,
    ClassGroupUpdateRequest,
    EnrollmentCreateRequest,
    EnrollmentTransferRequest,
    EnrollmentWithdrawRequest,
    SubjectCreateRequest,
    SubjectOfferingCreateRequest,
    SubjectOfferingUpdateRequest,
    SubjectUpdateRequest,
    TermCreateRequest,
    TermUpdateRequest,
    YearLevelCreateRequest,
    YearLevelUpdateRequest,
)
from app.services.audit import record_audit_event


# --- Academic Years ---
def create_academic_year(
    db: Session,
    *,
    school_id: uuid.UUID,
    payload: AcademicYearCreateRequest,
    actor_user_id: uuid.UUID,
) -> AcademicYear:
    if academic_repo.get_academic_year_by_name(db, school_id=school_id, name=payload.name):
        raise AppError(
            status_code=409,
            code="ACADEMIC_YEAR_EXISTS",
            message="An academic year with this name already exists in this school.",
        )

    year = AcademicYear(
        school_id=school_id,
        name=payload.name.strip(),
        start_date=payload.start_date,
        end_date=payload.end_date,
        status="active",
    )
    db.add(year)
    db.flush()
    record_audit_event(
        db,
        action="academic_year.created",
        target_type="academic_year",
        target_id=year.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={"name": year.name},
    )
    db.commit()
    db.refresh(year)
    return year


def update_academic_year(
    db: Session,
    *,
    school_id: uuid.UUID,
    academic_year_id: uuid.UUID,
    payload: AcademicYearUpdateRequest,
    actor_user_id: uuid.UUID,
) -> AcademicYear:
    year = academic_repo.get_academic_year(
        db, school_id=school_id, academic_year_id=academic_year_id
    )
    if year is None:
        raise AppError(404, "ACADEMIC_YEAR_NOT_FOUND", "Academic year not found.")

    new_start = payload.start_date or year.start_date
    new_end = payload.end_date or year.end_date
    if new_end <= new_start:
        raise AppError(422, "INVALID_DATE_RANGE", "end_date must be after start_date.")

    if payload.name is not None:
        existing = academic_repo.get_academic_year_by_name(
            db, school_id=school_id, name=payload.name
        )
        if existing is not None and existing.id != year.id:
            raise AppError(
                409,
                "ACADEMIC_YEAR_EXISTS",
                "An academic year with this name already exists in this school.",
            )
        year.name = payload.name.strip()
    year.start_date = new_start
    year.end_date = new_end
    if payload.status is not None:
        year.status = payload.status

    record_audit_event(
        db,
        action="academic_year.updated",
        target_type="academic_year",
        target_id=year.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={"name": year.name, "status": year.status},
    )
    db.commit()
    db.refresh(year)
    return year


# --- Terms ---
def create_term(
    db: Session,
    *,
    school_id: uuid.UUID,
    payload: TermCreateRequest,
    actor_user_id: uuid.UUID,
) -> Term:
    year = academic_repo.get_academic_year(
        db, school_id=school_id, academic_year_id=payload.academic_year_id
    )
    if year is None:
        raise AppError(404, "ACADEMIC_YEAR_NOT_FOUND", "Academic year not found.")

    if payload.start_date < year.start_date or payload.end_date > year.end_date:
        raise AppError(
            422,
            "TERM_OUTSIDE_ACADEMIC_YEAR",
            "Term dates must fall within the academic year date range.",
        )

    if academic_repo.get_term_by_year_and_name(
        db, school_id=school_id, academic_year_id=year.id, name=payload.name
    ):
        raise AppError(
            409,
            "TERM_EXISTS",
            "A term with this name already exists in this academic year.",
        )

    term = Term(
        school_id=school_id,
        academic_year_id=year.id,
        name=payload.name.strip(),
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    db.add(term)
    db.flush()
    record_audit_event(
        db,
        action="term.created",
        target_type="term",
        target_id=term.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={"name": term.name, "academic_year_id": str(year.id)},
    )
    db.commit()
    db.refresh(term)
    return term


def update_term(
    db: Session,
    *,
    school_id: uuid.UUID,
    term_id: uuid.UUID,
    payload: TermUpdateRequest,
    actor_user_id: uuid.UUID,
) -> Term:
    term = academic_repo.get_term(db, school_id=school_id, term_id=term_id)
    if term is None:
        raise AppError(404, "TERM_NOT_FOUND", "Term not found.")

    year = academic_repo.get_academic_year(
        db, school_id=school_id, academic_year_id=term.academic_year_id
    )
    assert year is not None

    new_start = payload.start_date or term.start_date
    new_end = payload.end_date or term.end_date
    if new_end <= new_start:
        raise AppError(422, "INVALID_DATE_RANGE", "end_date must be after start_date.")
    if new_start < year.start_date or new_end > year.end_date:
        raise AppError(
            422,
            "TERM_OUTSIDE_ACADEMIC_YEAR",
            "Term dates must fall within the academic year date range.",
        )

    if payload.name is not None:
        term.name = payload.name.strip()
    term.start_date = new_start
    term.end_date = new_end

    record_audit_event(
        db,
        action="term.updated",
        target_type="term",
        target_id=term.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={"name": term.name},
    )
    db.commit()
    db.refresh(term)
    return term


# --- Year Levels ---
def create_year_level(
    db: Session,
    *,
    school_id: uuid.UUID,
    payload: YearLevelCreateRequest,
    actor_user_id: uuid.UUID,
) -> YearLevel:
    if academic_repo.get_year_level_by_name(db, school_id=school_id, name=payload.name):
        raise AppError(
            409,
            "YEAR_LEVEL_EXISTS",
            "A year level with this name already exists in this school.",
        )

    level = YearLevel(
        school_id=school_id,
        name=payload.name.strip(),
        display_order=payload.display_order,
    )
    db.add(level)
    db.flush()
    record_audit_event(
        db,
        action="year_level.created",
        target_type="year_level",
        target_id=level.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={"name": level.name},
    )
    db.commit()
    db.refresh(level)
    return level


def update_year_level(
    db: Session,
    *,
    school_id: uuid.UUID,
    year_level_id: uuid.UUID,
    payload: YearLevelUpdateRequest,
    actor_user_id: uuid.UUID,
) -> YearLevel:
    level = academic_repo.get_year_level(
        db, school_id=school_id, year_level_id=year_level_id
    )
    if level is None:
        raise AppError(404, "YEAR_LEVEL_NOT_FOUND", "Year level not found.")

    if payload.name is not None:
        level.name = payload.name.strip()
    if payload.display_order is not None:
        level.display_order = payload.display_order

    record_audit_event(
        db,
        action="year_level.updated",
        target_type="year_level",
        target_id=level.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={"name": level.name, "display_order": level.display_order},
    )
    db.commit()
    db.refresh(level)
    return level


# --- Class Groups ---
def create_class_group(
    db: Session,
    *,
    school_id: uuid.UUID,
    payload: ClassGroupCreateRequest,
    actor_user_id: uuid.UUID,
) -> ClassGroup:
    year = academic_repo.get_academic_year(
        db, school_id=school_id, academic_year_id=payload.academic_year_id
    )
    if year is None:
        raise AppError(404, "ACADEMIC_YEAR_NOT_FOUND", "Academic year not found.")

    level = academic_repo.get_year_level(
        db, school_id=school_id, year_level_id=payload.year_level_id
    )
    if level is None:
        raise AppError(404, "YEAR_LEVEL_NOT_FOUND", "Year level not found.")

    if academic_repo.get_class_group_by_year_and_name(
        db, school_id=school_id, academic_year_id=year.id, name=payload.name
    ):
        raise AppError(
            409,
            "CLASS_GROUP_EXISTS",
            "A class group with this name already exists in this academic year.",
        )

    group = ClassGroup(
        school_id=school_id,
        academic_year_id=year.id,
        year_level_id=level.id,
        name=payload.name.strip(),
    )
    db.add(group)
    db.flush()
    record_audit_event(
        db,
        action="class_group.created",
        target_type="class_group",
        target_id=group.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={"name": group.name, "academic_year_id": str(year.id)},
    )
    db.commit()
    db.refresh(group)
    return group


def update_class_group(
    db: Session,
    *,
    school_id: uuid.UUID,
    class_group_id: uuid.UUID,
    payload: ClassGroupUpdateRequest,
    actor_user_id: uuid.UUID,
) -> ClassGroup:
    group = academic_repo.get_class_group(
        db, school_id=school_id, class_group_id=class_group_id
    )
    if group is None:
        raise AppError(404, "CLASS_GROUP_NOT_FOUND", "Class group not found.")

    if payload.name is not None:
        group.name = payload.name.strip()

    record_audit_event(
        db,
        action="class_group.updated",
        target_type="class_group",
        target_id=group.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={"name": group.name},
    )
    db.commit()
    db.refresh(group)
    return group


# --- Subjects ---
def create_subject(
    db: Session,
    *,
    school_id: uuid.UUID,
    payload: SubjectCreateRequest,
    actor_user_id: uuid.UUID,
) -> Subject:
    code = payload.code.strip().upper()
    if academic_repo.get_subject_by_code(db, school_id=school_id, code=code):
        raise AppError(
            409,
            "SUBJECT_CODE_EXISTS",
            "A subject with this code already exists in this school.",
        )

    subject = Subject(school_id=school_id, code=code, name=payload.name.strip())
    db.add(subject)
    db.flush()
    record_audit_event(
        db,
        action="subject.created",
        target_type="subject",
        target_id=subject.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={"code": subject.code, "name": subject.name},
    )
    db.commit()
    db.refresh(subject)
    return subject


def update_subject(
    db: Session,
    *,
    school_id: uuid.UUID,
    subject_id: uuid.UUID,
    payload: SubjectUpdateRequest,
    actor_user_id: uuid.UUID,
) -> Subject:
    subject = academic_repo.get_subject(
        db, school_id=school_id, subject_id=subject_id
    )
    if subject is None:
        raise AppError(404, "SUBJECT_NOT_FOUND", "Subject not found.")

    if payload.name is not None:
        subject.name = payload.name.strip()

    record_audit_event(
        db,
        action="subject.updated",
        target_type="subject",
        target_id=subject.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={"code": subject.code, "name": subject.name},
    )
    db.commit()
    db.refresh(subject)
    return subject


# --- Subject Offerings & Teacher Assignments ---
def _validate_active_school_teacher(
    db: Session, *, school_id: uuid.UUID, teacher_user_id: uuid.UUID
) -> None:
    membership = membership_repo.get_user_membership_in_school(
        db, user_id=teacher_user_id, school_id=school_id
    )
    if membership is None or membership.role != "teacher" or membership.status != "active":
        raise AppError(
            422,
            "INVALID_TEACHER_ASSIGNMENT",
            "Assigned user must be an active teacher in this school.",
        )


def create_subject_offering(
    db: Session,
    *,
    school_id: uuid.UUID,
    payload: SubjectOfferingCreateRequest,
    actor_user_id: uuid.UUID,
) -> tuple[SubjectOffering, list[uuid.UUID]]:
    group = academic_repo.get_class_group(
        db, school_id=school_id, class_group_id=payload.class_group_id
    )
    if group is None:
        raise AppError(404, "CLASS_GROUP_NOT_FOUND", "Class group not found.")

    subject = academic_repo.get_subject(
        db, school_id=school_id, subject_id=payload.subject_id
    )
    if subject is None:
        raise AppError(404, "SUBJECT_NOT_FOUND", "Subject not found.")

    if payload.term_id is not None:
        term = academic_repo.get_term(
            db, school_id=school_id, term_id=payload.term_id
        )
        if term is None or term.academic_year_id != group.academic_year_id:
            raise AppError(
                422,
                "INVALID_TERM",
                "Term must belong to the same school and academic year as the class group.",
            )

    if academic_repo.get_duplicate_subject_offering(
        db,
        school_id=school_id,
        class_group_id=group.id,
        subject_id=subject.id,
        term_id=payload.term_id,
    ):
        raise AppError(
            409,
            "SUBJECT_OFFERING_EXISTS",
            "This subject offering already exists for the selected class group and term.",
        )

    unique_teacher_ids = list(dict.fromkeys(payload.teacher_user_ids))
    for teacher_id in unique_teacher_ids:
        _validate_active_school_teacher(
            db, school_id=school_id, teacher_user_id=teacher_id
        )

    offering = SubjectOffering(
        school_id=school_id,
        class_group_id=group.id,
        subject_id=subject.id,
        term_id=payload.term_id,
        status="active",
    )
    db.add(offering)
    db.flush()

    for teacher_id in unique_teacher_ids:
        db.add(
            OfferingTeacher(
                school_id=school_id,
                subject_offering_id=offering.id,
                teacher_user_id=teacher_id,
            )
        )

    record_audit_event(
        db,
        action="subject_offering.created",
        target_type="subject_offering",
        target_id=offering.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={
            "class_group_id": str(group.id),
            "subject_id": str(subject.id),
            "teacher_user_ids": [str(tid) for tid in unique_teacher_ids],
        },
    )
    db.commit()
    db.refresh(offering)
    return offering, unique_teacher_ids


def update_subject_offering(
    db: Session,
    *,
    school_id: uuid.UUID,
    offering_id: uuid.UUID,
    payload: SubjectOfferingUpdateRequest,
    actor_user_id: uuid.UUID,
) -> tuple[SubjectOffering, list[uuid.UUID]]:
    offering = academic_repo.get_subject_offering(
        db, school_id=school_id, offering_id=offering_id
    )
    if offering is None:
        raise AppError(404, "SUBJECT_OFFERING_NOT_FOUND", "Subject offering not found.")

    if payload.status is not None:
        offering.status = payload.status
        record_audit_event(
            db,
            action="subject_offering.updated",
            target_type="subject_offering",
            target_id=offering.id,
            actor_user_id=actor_user_id,
            school_id=school_id,
            metadata={"status": offering.status},
        )
        db.commit()
        db.refresh(offering)

    teacher_ids = academic_repo.list_offering_teacher_ids(
        db, school_id=school_id, subject_offering_id=offering.id
    )
    return offering, teacher_ids


def assign_teacher_to_offering(
    db: Session,
    *,
    school_id: uuid.UUID,
    offering_id: uuid.UUID,
    teacher_user_id: uuid.UUID,
    actor_user_id: uuid.UUID,
) -> tuple[SubjectOffering, list[uuid.UUID]]:
    offering = academic_repo.get_subject_offering(
        db, school_id=school_id, offering_id=offering_id
    )
    if offering is None:
        raise AppError(404, "SUBJECT_OFFERING_NOT_FOUND", "Subject offering not found.")

    _validate_active_school_teacher(
        db, school_id=school_id, teacher_user_id=teacher_user_id
    )

    if academic_repo.get_offering_teacher(
        db,
        school_id=school_id,
        subject_offering_id=offering.id,
        teacher_user_id=teacher_user_id,
    ):
        raise AppError(
            409,
            "TEACHER_ALREADY_ASSIGNED",
            "Teacher is already assigned to this subject offering.",
        )

    db.add(
        OfferingTeacher(
            school_id=school_id,
            subject_offering_id=offering.id,
            teacher_user_id=teacher_user_id,
        )
    )
    record_audit_event(
        db,
        action="offering_teacher.assigned",
        target_type="subject_offering",
        target_id=offering.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={"teacher_user_id": str(teacher_user_id)},
    )
    db.commit()
    teacher_ids = academic_repo.list_offering_teacher_ids(
        db, school_id=school_id, subject_offering_id=offering.id
    )
    return offering, teacher_ids


# --- Enrollments (SCH-04: preserve history on transfer & withdrawal) ---
def _validate_active_school_student(
    db: Session, *, school_id: uuid.UUID, student_user_id: uuid.UUID
) -> None:
    membership = membership_repo.get_user_membership_in_school(
        db, user_id=student_user_id, school_id=school_id
    )
    if membership is None or membership.role != "student" or membership.status != "active":
        raise AppError(
            422,
            "INVALID_STUDENT_ENROLLMENT",
            "User must have an active student membership in this school.",
        )


def create_enrollment(
    db: Session,
    *,
    school_id: uuid.UUID,
    payload: EnrollmentCreateRequest,
    actor_user_id: uuid.UUID,
) -> Enrollment:
    _validate_active_school_student(
        db, school_id=school_id, student_user_id=payload.student_user_id
    )

    group = academic_repo.get_class_group(
        db, school_id=school_id, class_group_id=payload.class_group_id
    )
    if group is None:
        raise AppError(404, "CLASS_GROUP_NOT_FOUND", "Class group not found.")

    if payload.subject_offering_id is not None:
        offering = academic_repo.get_subject_offering(
            db, school_id=school_id, offering_id=payload.subject_offering_id
        )
        if offering is None or offering.class_group_id != group.id:
            raise AppError(
                422,
                "INVALID_SUBJECT_OFFERING",
                "Subject offering must belong to the selected class group and school.",
            )

    existing_active = academic_repo.get_active_enrollment(
        db,
        school_id=school_id,
        student_user_id=payload.student_user_id,
        academic_year_id=group.academic_year_id,
        subject_offering_id=payload.subject_offering_id,
    )
    if existing_active is not None:
        raise AppError(
            409,
            "ENROLLMENT_ALREADY_ACTIVE",
            "Student already has an active enrollment for this scope. Use transfer instead.",
        )

    enrollment = Enrollment(
        school_id=school_id,
        student_user_id=payload.student_user_id,
        academic_year_id=group.academic_year_id,
        class_group_id=group.id,
        subject_offering_id=payload.subject_offering_id,
        status="active",
        effective_from=payload.effective_from,
    )
    db.add(enrollment)
    db.flush()
    record_audit_event(
        db,
        action="enrollment.created",
        target_type="enrollment",
        target_id=enrollment.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={
            "student_user_id": str(enrollment.student_user_id),
            "class_group_id": str(enrollment.class_group_id),
            "subject_offering_id": (
                str(enrollment.subject_offering_id)
                if enrollment.subject_offering_id
                else None
            ),
        },
    )
    db.commit()
    db.refresh(enrollment)
    return enrollment


def transfer_enrollment(
    db: Session,
    *,
    school_id: uuid.UUID,
    enrollment_id: uuid.UUID,
    payload: EnrollmentTransferRequest,
    actor_user_id: uuid.UUID,
) -> tuple[Enrollment, Enrollment]:
    """SCH-04: Mark previous enrollment transferred and create a new active row."""
    enrollment = academic_repo.get_enrollment(
        db, school_id=school_id, enrollment_id=enrollment_id
    )
    if enrollment is None:
        raise AppError(404, "ENROLLMENT_NOT_FOUND", "Enrollment not found.")

    if enrollment.status != "active":
        raise AppError(
            409,
            "INVALID_STATE_TRANSITION",
            "Only an active enrollment can be transferred.",
        )

    if payload.effective_date < enrollment.effective_from:
        raise AppError(
            422,
            "INVALID_DATE_RANGE",
            "Transfer effective_date cannot be earlier than effective_from.",
        )

    target_group = academic_repo.get_class_group(
        db, school_id=school_id, class_group_id=payload.target_class_group_id
    )
    if target_group is None:
        raise AppError(404, "CLASS_GROUP_NOT_FOUND", "Target class group not found.")

    if payload.target_subject_offering_id is not None:
        offering = academic_repo.get_subject_offering(
            db, school_id=school_id, offering_id=payload.target_subject_offering_id
        )
        if offering is None or offering.class_group_id != target_group.id:
            raise AppError(
                422,
                "INVALID_SUBJECT_OFFERING",
                "Target subject offering must belong to the target class group.",
            )

    enrollment.status = "transferred"
    enrollment.effective_to = payload.effective_date

    new_enrollment = Enrollment(
        school_id=school_id,
        student_user_id=enrollment.student_user_id,
        academic_year_id=target_group.academic_year_id,
        class_group_id=target_group.id,
        subject_offering_id=payload.target_subject_offering_id,
        status="active",
        effective_from=payload.effective_date,
    )
    db.add(new_enrollment)
    db.flush()

    record_audit_event(
        db,
        action="enrollment.transferred",
        target_type="enrollment",
        target_id=new_enrollment.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={
            "student_user_id": str(enrollment.student_user_id),
            "previous_enrollment_id": str(enrollment.id),
            "previous_class_group_id": str(enrollment.class_group_id),
            "new_class_group_id": str(new_enrollment.class_group_id),
            "effective_date": payload.effective_date.isoformat(),
        },
    )
    db.commit()
    db.refresh(enrollment)
    db.refresh(new_enrollment)
    return enrollment, new_enrollment


def withdraw_enrollment(
    db: Session,
    *,
    school_id: uuid.UUID,
    enrollment_id: uuid.UUID,
    payload: EnrollmentWithdrawRequest,
    actor_user_id: uuid.UUID,
) -> Enrollment:
    """SCH-04: Mark enrollment withdrawn while keeping historical record intact."""
    enrollment = academic_repo.get_enrollment(
        db, school_id=school_id, enrollment_id=enrollment_id
    )
    if enrollment is None:
        raise AppError(404, "ENROLLMENT_NOT_FOUND", "Enrollment not found.")

    if enrollment.status != "active":
        raise AppError(
            409,
            "INVALID_STATE_TRANSITION",
            "Only an active enrollment can be withdrawn.",
        )

    if payload.effective_date < enrollment.effective_from:
        raise AppError(
            422,
            "INVALID_DATE_RANGE",
            "Withdrawal effective_date cannot be earlier than effective_from.",
        )

    enrollment.status = "withdrawn"
    enrollment.effective_to = payload.effective_date

    record_audit_event(
        db,
        action="enrollment.withdrawn",
        target_type="enrollment",
        target_id=enrollment.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={
            "student_user_id": str(enrollment.student_user_id),
            "class_group_id": str(enrollment.class_group_id),
            "effective_date": payload.effective_date.isoformat(),
        },
    )
    db.commit()
    db.refresh(enrollment)
    return enrollment
