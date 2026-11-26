import uuid

from sqlalchemy import select
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


def list_academic_years(db: Session, *, school_id: uuid.UUID) -> list[AcademicYear]:
    return list(
        db.scalars(
            select(AcademicYear)
            .where(AcademicYear.school_id == school_id)
            .order_by(AcademicYear.start_date.desc())
        ).all()
    )


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
    db: Session, *, school_id: uuid.UUID, academic_year_id: uuid.UUID | None = None
) -> list[Term]:
    stmt = select(Term).where(Term.school_id == school_id)
    if academic_year_id is not None:
        stmt = stmt.where(Term.academic_year_id == academic_year_id)
    return list(db.scalars(stmt.order_by(Term.start_date.asc())).all())


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


def list_year_levels(db: Session, *, school_id: uuid.UUID) -> list[YearLevel]:
    return list(
        db.scalars(
            select(YearLevel)
            .where(YearLevel.school_id == school_id)
            .order_by(YearLevel.display_order.asc(), YearLevel.name.asc())
        ).all()
    )


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


def list_class_groups(
    db: Session, *, school_id: uuid.UUID, academic_year_id: uuid.UUID | None = None
) -> list[ClassGroup]:
    stmt = select(ClassGroup).where(ClassGroup.school_id == school_id)
    if academic_year_id is not None:
        stmt = stmt.where(ClassGroup.academic_year_id == academic_year_id)
    return list(db.scalars(stmt.order_by(ClassGroup.name.asc())).all())


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


def list_subjects(db: Session, *, school_id: uuid.UUID) -> list[Subject]:
    return list(
        db.scalars(
            select(Subject)
            .where(Subject.school_id == school_id)
            .order_by(Subject.code.asc())
        ).all()
    )


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
    db: Session, *, school_id: uuid.UUID, class_group_id: uuid.UUID | None = None
) -> list[SubjectOffering]:
    stmt = select(SubjectOffering).where(SubjectOffering.school_id == school_id)
    if class_group_id is not None:
        stmt = stmt.where(SubjectOffering.class_group_id == class_group_id)
    return list(db.scalars(stmt.order_by(SubjectOffering.created_at.desc())).all())


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
    status: str | None = None,
) -> list[Enrollment]:
    stmt = select(Enrollment).where(Enrollment.school_id == school_id)
    if student_user_id is not None:
        stmt = stmt.where(Enrollment.student_user_id == student_user_id)
    if class_group_id is not None:
        stmt = stmt.where(Enrollment.class_group_id == class_group_id)
    if status is not None:
        stmt = stmt.where(Enrollment.status == status)
    return list(db.scalars(stmt.order_by(Enrollment.created_at.desc())).all())
