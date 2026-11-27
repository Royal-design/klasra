import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

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
from app.models.assessment import Assessment
from app.models.assignment import Assignment
from app.models.attendance import AttendanceRecord
from app.models.lesson import Lesson
from app.repositories.pagination import count_and_paginate_scalars, escape_like


# --- Academic Years ---
def get_academic_year(
    db: Session, *, school_id: uuid.UUID, academic_year_id: uuid.UUID
) -> AcademicYear | None:
    return db.scalar(
        select(AcademicYear).where(
            AcademicYear.id == academic_year_id,
            AcademicYear.school_id == school_id,
        )
    )


def get_academic_year_by_name(
    db: Session, *, school_id: uuid.UUID, name: str
) -> AcademicYear | None:
    return db.scalar(
        select(AcademicYear).where(
            AcademicYear.school_id == school_id,
            AcademicYear.name == name.strip(),
        )
    )


def list_academic_years(
    db: Session,
    *,
    school_id: uuid.UUID,
    status: str | None = None,
    q: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[AcademicYear], int]:
    stmt = select(AcademicYear).where(AcademicYear.school_id == school_id)
    if status is not None:
        stmt = stmt.where(AcademicYear.status == status)
    if q and q.strip():
        pattern = f"%{escape_like(q.strip())}%"
        stmt = stmt.where(AcademicYear.name.ilike(pattern, escape="\\"))
    stmt = stmt.order_by(AcademicYear.start_date.desc())
    return count_and_paginate_scalars(db, stmt, offset=offset, limit=limit)


# --- Terms ---
def get_term(
    db: Session, *, school_id: uuid.UUID, term_id: uuid.UUID
) -> Term | None:
    return db.scalar(
        select(Term).where(Term.id == term_id, Term.school_id == school_id)
    )


def get_term_by_year_and_name(
    db: Session, *, school_id: uuid.UUID, academic_year_id: uuid.UUID, name: str
) -> Term | None:
    return db.scalar(
        select(Term).where(
            Term.school_id == school_id,
            Term.academic_year_id == academic_year_id,
            Term.name == name.strip(),
        )
    )


def list_terms(
    db: Session,
    *,
    school_id: uuid.UUID,
    academic_year_id: uuid.UUID | None = None,
    q: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Term], int]:
    stmt = select(Term).where(Term.school_id == school_id)
    if academic_year_id is not None:
        stmt = stmt.where(Term.academic_year_id == academic_year_id)
    if q and q.strip():
        pattern = f"%{escape_like(q.strip())}%"
        stmt = stmt.where(Term.name.ilike(pattern, escape="\\"))
    stmt = stmt.order_by(Term.start_date.asc())
    return count_and_paginate_scalars(db, stmt, offset=offset, limit=limit)


# --- Year Levels ---
def get_year_level(
    db: Session, *, school_id: uuid.UUID, year_level_id: uuid.UUID
) -> YearLevel | None:
    return db.scalar(
        select(YearLevel).where(
            YearLevel.id == year_level_id, YearLevel.school_id == school_id
        )
    )


def get_year_level_by_name(
    db: Session, *, school_id: uuid.UUID, name: str
) -> YearLevel | None:
    return db.scalar(
        select(YearLevel).where(
            YearLevel.school_id == school_id, YearLevel.name == name.strip()
        )
    )


def list_year_levels(
    db: Session,
    *,
    school_id: uuid.UUID,
    q: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[YearLevel], int]:
    stmt = select(YearLevel).where(YearLevel.school_id == school_id)
    if q and q.strip():
        pattern = f"%{escape_like(q.strip())}%"
        stmt = stmt.where(YearLevel.name.ilike(pattern, escape="\\"))
    stmt = stmt.order_by(YearLevel.display_order.asc(), YearLevel.name.asc())
    return count_and_paginate_scalars(db, stmt, offset=offset, limit=limit)


# --- Class Groups ---
def get_class_group(
    db: Session, *, school_id: uuid.UUID, class_group_id: uuid.UUID
) -> ClassGroup | None:
    return db.scalar(
        select(ClassGroup).where(
            ClassGroup.id == class_group_id, ClassGroup.school_id == school_id
        )
    )


def get_class_group_by_year_and_name(
    db: Session, *, school_id: uuid.UUID, academic_year_id: uuid.UUID, name: str
) -> ClassGroup | None:
    return db.scalar(
        select(ClassGroup).where(
            ClassGroup.school_id == school_id,
            ClassGroup.academic_year_id == academic_year_id,
            ClassGroup.name == name.strip(),
        )
    )


def get_class_group_by_year_level_and_name(
    db: Session,
    *,
    school_id: uuid.UUID,
    academic_year_id: uuid.UUID,
    year_level_id: uuid.UUID,
    name: str,
) -> ClassGroup | None:
    return db.scalar(
        select(ClassGroup).where(
            ClassGroup.school_id == school_id,
            ClassGroup.academic_year_id == academic_year_id,
            ClassGroup.year_level_id == year_level_id,
            ClassGroup.name == name.strip(),
        )
    )


def list_class_groups(
    db: Session,
    *,
    school_id: uuid.UUID,
    academic_year_id: uuid.UUID | None = None,
    year_level_id: uuid.UUID | None = None,
    q: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[ClassGroup], int]:
    stmt = (
        select(ClassGroup)
        .join(YearLevel, ClassGroup.year_level_id == YearLevel.id)
        .where(ClassGroup.school_id == school_id)
    )
    if academic_year_id is not None:
        stmt = stmt.where(ClassGroup.academic_year_id == academic_year_id)
    if year_level_id is not None:
        stmt = stmt.where(ClassGroup.year_level_id == year_level_id)
    if q and q.strip():
        pattern = f"%{escape_like(q.strip())}%"
        stmt = stmt.where(ClassGroup.name.ilike(pattern, escape="\\"))
    stmt = stmt.order_by(
        YearLevel.display_order.asc(), YearLevel.name.asc(), ClassGroup.name.asc()
    )
    return count_and_paginate_scalars(db, stmt, offset=offset, limit=limit)


# --- Subjects ---
def get_subject(
    db: Session, *, school_id: uuid.UUID, subject_id: uuid.UUID
) -> Subject | None:
    return db.scalar(
        select(Subject).where(
            Subject.id == subject_id, Subject.school_id == school_id
        )
    )


def get_subject_by_code(
    db: Session, *, school_id: uuid.UUID, code: str
) -> Subject | None:
    return db.scalar(
        select(Subject).where(
            Subject.school_id == school_id, Subject.code == code.strip().upper()
        )
    )


def list_subjects(
    db: Session,
    *,
    school_id: uuid.UUID,
    q: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Subject], int]:
    stmt = select(Subject).where(Subject.school_id == school_id)
    if q and q.strip():
        pattern = f"%{escape_like(q.strip())}%"
        stmt = stmt.where(
            or_(
                Subject.code.ilike(pattern, escape="\\"),
                Subject.name.ilike(pattern, escape="\\"),
            )
        )
    stmt = stmt.order_by(Subject.code.asc())
    return count_and_paginate_scalars(db, stmt, offset=offset, limit=limit)


# --- Subject Offerings & Teacher Assignments ---
def get_subject_offering(
    db: Session, *, school_id: uuid.UUID, offering_id: uuid.UUID
) -> SubjectOffering | None:
    return db.scalar(
        select(SubjectOffering).where(
            SubjectOffering.id == offering_id,
            SubjectOffering.school_id == school_id,
        )
    )


def get_duplicate_subject_offering(
    db: Session,
    *,
    school_id: uuid.UUID,
    class_group_id: uuid.UUID,
    subject_id: uuid.UUID,
    term_id: uuid.UUID | None,
) -> SubjectOffering | None:
    stmt = select(SubjectOffering).where(
        SubjectOffering.school_id == school_id,
        SubjectOffering.class_group_id == class_group_id,
        SubjectOffering.subject_id == subject_id,
    )
    if term_id is None:
        stmt = stmt.where(SubjectOffering.term_id.is_(None))
    else:
        stmt = stmt.where(SubjectOffering.term_id == term_id)
    return db.scalar(stmt)


def list_subject_offerings(
    db: Session,
    *,
    school_id: uuid.UUID,
    class_group_id: uuid.UUID | None = None,
    subject_id: uuid.UUID | None = None,
    term_id: uuid.UUID | None = None,
    status: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[SubjectOffering], int]:
    stmt = select(SubjectOffering).where(SubjectOffering.school_id == school_id)
    if class_group_id is not None:
        stmt = stmt.where(SubjectOffering.class_group_id == class_group_id)
    if subject_id is not None:
        stmt = stmt.where(SubjectOffering.subject_id == subject_id)
    if term_id is not None:
        stmt = stmt.where(SubjectOffering.term_id == term_id)
    if status is not None:
        stmt = stmt.where(SubjectOffering.status == status)
    stmt = stmt.order_by(SubjectOffering.created_at.desc())
    return count_and_paginate_scalars(db, stmt, offset=offset, limit=limit)


def get_offering_teacher(
    db: Session,
    *,
    school_id: uuid.UUID,
    subject_offering_id: uuid.UUID,
    teacher_user_id: uuid.UUID,
) -> OfferingTeacher | None:
    return db.scalar(
        select(OfferingTeacher).where(
            OfferingTeacher.school_id == school_id,
            OfferingTeacher.subject_offering_id == subject_offering_id,
            OfferingTeacher.teacher_user_id == teacher_user_id,
        )
    )


def list_offering_teacher_ids(
    db: Session, *, school_id: uuid.UUID, subject_offering_id: uuid.UUID
) -> list[uuid.UUID]:
    return list(
        db.scalars(
            select(OfferingTeacher.teacher_user_id).where(
                OfferingTeacher.school_id == school_id,
                OfferingTeacher.subject_offering_id == subject_offering_id,
            )
        ).all()
    )


# --- Enrollments ---
def get_enrollment(
    db: Session, *, school_id: uuid.UUID, enrollment_id: uuid.UUID
) -> Enrollment | None:
    return db.scalar(
        select(Enrollment).where(
            Enrollment.id == enrollment_id,
            Enrollment.school_id == school_id,
        )
    )


def get_active_enrollment(
    db: Session,
    *,
    school_id: uuid.UUID,
    student_user_id: uuid.UUID,
    academic_year_id: uuid.UUID,
    subject_offering_id: uuid.UUID | None,
) -> Enrollment | None:
    stmt = select(Enrollment).where(
        Enrollment.school_id == school_id,
        Enrollment.student_user_id == student_user_id,
        Enrollment.academic_year_id == academic_year_id,
        Enrollment.status == "active",
    )
    if subject_offering_id is None:
        stmt = stmt.where(Enrollment.subject_offering_id.is_(None))
    else:
        stmt = stmt.where(Enrollment.subject_offering_id == subject_offering_id)
    return db.scalar(stmt)


def list_enrollments(
    db: Session,
    *,
    school_id: uuid.UUID,
    student_user_id: uuid.UUID | None = None,
    class_group_id: uuid.UUID | None = None,
    academic_year_id: uuid.UUID | None = None,
    status: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Enrollment], int]:
    stmt = select(Enrollment).where(Enrollment.school_id == school_id)
    if student_user_id is not None:
        stmt = stmt.where(Enrollment.student_user_id == student_user_id)
    if class_group_id is not None:
        stmt = stmt.where(Enrollment.class_group_id == class_group_id)
    if academic_year_id is not None:
        stmt = stmt.where(Enrollment.academic_year_id == academic_year_id)
    if status is not None:
        stmt = stmt.where(Enrollment.status == status)
    stmt = stmt.order_by(Enrollment.created_at.desc())
    return count_and_paginate_scalars(db, stmt, offset=offset, limit=limit)


def list_all_year_levels(db: Session, *, school_id: uuid.UUID) -> list[YearLevel]:
    return list(
        db.scalars(
            select(YearLevel)
            .where(YearLevel.school_id == school_id)
            .order_by(YearLevel.display_order.asc(), YearLevel.name.asc())
        ).all()
    )


# --- Safe-delete dependency counts (school-scoped) ---
def count_academic_year_dependencies(
    db: Session, *, school_id: uuid.UUID, academic_year_id: uuid.UUID
) -> dict[str, int]:
    terms = db.scalar(
        select(func.count(Term.id)).where(
            Term.school_id == school_id, Term.academic_year_id == academic_year_id
        )
    ) or 0
    class_groups = db.scalar(
        select(func.count(ClassGroup.id)).where(
            ClassGroup.school_id == school_id,
            ClassGroup.academic_year_id == academic_year_id,
        )
    ) or 0
    enrollments = db.scalar(
        select(func.count(Enrollment.id)).where(
            Enrollment.school_id == school_id,
            Enrollment.academic_year_id == academic_year_id,
        )
    ) or 0
    return {
        "terms": int(terms),
        "class groups": int(class_groups),
        "enrollments": int(enrollments),
    }


def count_term_dependencies(
    db: Session, *, school_id: uuid.UUID, term_id: uuid.UUID
) -> dict[str, int]:
    offerings = db.scalar(
        select(func.count(SubjectOffering.id)).where(
            SubjectOffering.school_id == school_id,
            SubjectOffering.term_id == term_id,
        )
    ) or 0
    return {"subject offerings": int(offerings)}


def count_year_level_dependencies(
    db: Session, *, school_id: uuid.UUID, year_level_id: uuid.UUID
) -> dict[str, int]:
    class_groups = db.scalar(
        select(func.count(ClassGroup.id)).where(
            ClassGroup.school_id == school_id,
            ClassGroup.year_level_id == year_level_id,
        )
    ) or 0
    return {"class groups": int(class_groups)}


def count_class_group_dependencies(
    db: Session, *, school_id: uuid.UUID, class_group_id: uuid.UUID
) -> dict[str, int]:
    offerings = db.scalar(
        select(func.count(SubjectOffering.id)).where(
            SubjectOffering.school_id == school_id,
            SubjectOffering.class_group_id == class_group_id,
        )
    ) or 0
    enrollments = db.scalar(
        select(func.count(Enrollment.id)).where(
            Enrollment.school_id == school_id,
            Enrollment.class_group_id == class_group_id,
        )
    ) or 0
    return {
        "subject offerings": int(offerings),
        "enrollments": int(enrollments),
    }


def count_subject_dependencies(
    db: Session, *, school_id: uuid.UUID, subject_id: uuid.UUID
) -> dict[str, int]:
    offerings = db.scalar(
        select(func.count(SubjectOffering.id)).where(
            SubjectOffering.school_id == school_id,
            SubjectOffering.subject_id == subject_id,
        )
    ) or 0
    return {"subject offerings": int(offerings)}


def count_subject_offering_dependencies(
    db: Session, *, school_id: uuid.UUID, offering_id: uuid.UUID
) -> dict[str, int]:
    enrollments = db.scalar(
        select(func.count(Enrollment.id)).where(
            Enrollment.school_id == school_id,
            Enrollment.subject_offering_id == offering_id,
        )
    ) or 0
    lessons = db.scalar(
        select(func.count(Lesson.id)).where(
            Lesson.school_id == school_id,
            Lesson.subject_offering_id == offering_id,
        )
    ) or 0
    assignments = db.scalar(
        select(func.count(Assignment.id)).where(
            Assignment.school_id == school_id,
            Assignment.subject_offering_id == offering_id,
        )
    ) or 0
    attendance = db.scalar(
        select(func.count(AttendanceRecord.id)).where(
            AttendanceRecord.school_id == school_id,
            AttendanceRecord.subject_offering_id == offering_id,
        )
    ) or 0
    assessments = db.scalar(
        select(func.count(Assessment.id)).where(
            Assessment.school_id == school_id,
            Assessment.subject_offering_id == offering_id,
        )
    ) or 0
    return {
        "enrollments": int(enrollments),
        "lessons": int(lessons),
        "assignments": int(assignments),
        "attendance records": int(attendance),
        "assessments": int(assessments),
    }
