import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import SchoolAuthContext, require_school_role
from app.db.session import get_db
from app.repositories import academic_repo
from app.schemas.academic import (
    AcademicYearCreateRequest,
    AcademicYearResponse,
    AcademicYearUpdateRequest,
    ClassGroupCreateRequest,
    ClassGroupResponse,
    ClassGroupUpdateRequest,
    EnrollmentCreateRequest,
    EnrollmentResponse,
    EnrollmentTransferRequest,
    EnrollmentTransferResponse,
    EnrollmentWithdrawRequest,
    OfferingTeacherAssignRequest,
    SubjectCreateRequest,
    SubjectOfferingCreateRequest,
    SubjectOfferingResponse,
    SubjectOfferingUpdateRequest,
    SubjectResponse,
    SubjectUpdateRequest,
    TermCreateRequest,
    TermResponse,
    TermUpdateRequest,
    YearLevelCreateRequest,
    YearLevelResponse,
    YearLevelUpdateRequest,
)
from app.schemas.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
    get_pagination_params,
)
from app.services import academic as academic_service

router = APIRouter(prefix="/schools/{school_id}", tags=["academic"])

require_school_admin = require_school_role({"school_admin"})


def _to_offering_response(offering, teacher_ids: list[uuid.UUID]) -> SubjectOfferingResponse:
    return SubjectOfferingResponse(
        id=offering.id,
        school_id=offering.school_id,
        class_group_id=offering.class_group_id,
        subject_id=offering.subject_id,
        term_id=offering.term_id,
        status=offering.status,
        teacher_user_ids=teacher_ids,
        created_at=offering.created_at,
        updated_at=offering.updated_at,
    )


# --- Academic Years ---
@router.post(
    "/academic-years",
    response_model=AcademicYearResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_academic_year_endpoint(
    payload: AcademicYearCreateRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> AcademicYearResponse:
    year = academic_service.create_academic_year(
        db,
        school_id=school_auth.school.id,
        payload=payload,
        actor_user_id=school_auth.user.id,
    )
    return AcademicYearResponse.model_validate(year)


@router.get("/academic-years", response_model=PaginatedResponse[AcademicYearResponse])
def list_academic_years_endpoint(
    year_status: str | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None, max_length=100),
    pagination: PaginationParams = Depends(get_pagination_params),
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> PaginatedResponse[AcademicYearResponse]:
    years, total = academic_repo.list_academic_years(
        db,
        school_id=school_auth.school.id,
        status=year_status,
        q=q,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [AcademicYearResponse.model_validate(y) for y in years],
        total=total,
        pagination=pagination,
    )


@router.patch(
    "/academic-years/{academic_year_id}",
    response_model=AcademicYearResponse,
)
def update_academic_year_endpoint(
    academic_year_id: uuid.UUID,
    payload: AcademicYearUpdateRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> AcademicYearResponse:
    year = academic_service.update_academic_year(
        db,
        school_id=school_auth.school.id,
        academic_year_id=academic_year_id,
        payload=payload,
        actor_user_id=school_auth.user.id,
    )
    return AcademicYearResponse.model_validate(year)


# --- Terms ---
@router.post(
    "/terms",
    response_model=TermResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_term_endpoint(
    payload: TermCreateRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> TermResponse:
    term = academic_service.create_term(
        db,
        school_id=school_auth.school.id,
        payload=payload,
        actor_user_id=school_auth.user.id,
    )
    return TermResponse.model_validate(term)


@router.get("/terms", response_model=PaginatedResponse[TermResponse])
def list_terms_endpoint(
    academic_year_id: uuid.UUID | None = Query(default=None),
    q: str | None = Query(default=None, max_length=100),
    pagination: PaginationParams = Depends(get_pagination_params),
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> PaginatedResponse[TermResponse]:
    terms, total = academic_repo.list_terms(
        db,
        school_id=school_auth.school.id,
        academic_year_id=academic_year_id,
        q=q,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [TermResponse.model_validate(t) for t in terms],
        total=total,
        pagination=pagination,
    )


@router.patch("/terms/{term_id}", response_model=TermResponse)
def update_term_endpoint(
    term_id: uuid.UUID,
    payload: TermUpdateRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> TermResponse:
    term = academic_service.update_term(
        db,
        school_id=school_auth.school.id,
        term_id=term_id,
        payload=payload,
        actor_user_id=school_auth.user.id,
    )
    return TermResponse.model_validate(term)


# --- Year Levels ---
@router.post(
    "/year-levels",
    response_model=YearLevelResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_year_level_endpoint(
    payload: YearLevelCreateRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> YearLevelResponse:
    level = academic_service.create_year_level(
        db,
        school_id=school_auth.school.id,
        payload=payload,
        actor_user_id=school_auth.user.id,
    )
    return YearLevelResponse.model_validate(level)


@router.get("/year-levels", response_model=PaginatedResponse[YearLevelResponse])
def list_year_levels_endpoint(
    q: str | None = Query(default=None, max_length=100),
    pagination: PaginationParams = Depends(get_pagination_params),
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> PaginatedResponse[YearLevelResponse]:
    levels, total = academic_repo.list_year_levels(
        db,
        school_id=school_auth.school.id,
        q=q,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [YearLevelResponse.model_validate(lvl) for lvl in levels],
        total=total,
        pagination=pagination,
    )


@router.patch("/year-levels/{year_level_id}", response_model=YearLevelResponse)
def update_year_level_endpoint(
    year_level_id: uuid.UUID,
    payload: YearLevelUpdateRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> YearLevelResponse:
    level = academic_service.update_year_level(
        db,
        school_id=school_auth.school.id,
        year_level_id=year_level_id,
        payload=payload,
        actor_user_id=school_auth.user.id,
    )
    return YearLevelResponse.model_validate(level)


# --- Class Groups ---
@router.post(
    "/class-groups",
    response_model=ClassGroupResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_class_group_endpoint(
    payload: ClassGroupCreateRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> ClassGroupResponse:
    group = academic_service.create_class_group(
        db,
        school_id=school_auth.school.id,
        payload=payload,
        actor_user_id=school_auth.user.id,
    )
    return ClassGroupResponse.model_validate(group)


@router.get("/class-groups", response_model=PaginatedResponse[ClassGroupResponse])
def list_class_groups_endpoint(
    academic_year_id: uuid.UUID | None = Query(default=None),
    year_level_id: uuid.UUID | None = Query(default=None),
    q: str | None = Query(default=None, max_length=100),
    pagination: PaginationParams = Depends(get_pagination_params),
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ClassGroupResponse]:
    groups, total = academic_repo.list_class_groups(
        db,
        school_id=school_auth.school.id,
        academic_year_id=academic_year_id,
        year_level_id=year_level_id,
        q=q,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [ClassGroupResponse.model_validate(g) for g in groups],
        total=total,
        pagination=pagination,
    )


@router.patch("/class-groups/{class_group_id}", response_model=ClassGroupResponse)
def update_class_group_endpoint(
    class_group_id: uuid.UUID,
    payload: ClassGroupUpdateRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> ClassGroupResponse:
    group = academic_service.update_class_group(
        db,
        school_id=school_auth.school.id,
        class_group_id=class_group_id,
        payload=payload,
        actor_user_id=school_auth.user.id,
    )
    return ClassGroupResponse.model_validate(group)


# --- Subjects ---
@router.post(
    "/subjects",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_subject_endpoint(
    payload: SubjectCreateRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> SubjectResponse:
    subject = academic_service.create_subject(
        db,
        school_id=school_auth.school.id,
        payload=payload,
        actor_user_id=school_auth.user.id,
    )
    return SubjectResponse.model_validate(subject)


@router.get("/subjects", response_model=PaginatedResponse[SubjectResponse])
def list_subjects_endpoint(
    q: str | None = Query(default=None, max_length=100, description="Search by code or name"),
    pagination: PaginationParams = Depends(get_pagination_params),
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> PaginatedResponse[SubjectResponse]:
    subjects, total = academic_repo.list_subjects(
        db,
        school_id=school_auth.school.id,
        q=q,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [SubjectResponse.model_validate(s) for s in subjects],
        total=total,
        pagination=pagination,
    )


@router.patch("/subjects/{subject_id}", response_model=SubjectResponse)
def update_subject_endpoint(
    subject_id: uuid.UUID,
    payload: SubjectUpdateRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> SubjectResponse:
    subject = academic_service.update_subject(
        db,
        school_id=school_auth.school.id,
        subject_id=subject_id,
        payload=payload,
        actor_user_id=school_auth.user.id,
    )
    return SubjectResponse.model_validate(subject)


# --- Subject Offerings & Teacher Assignments ---
@router.post(
    "/subject-offerings",
    response_model=SubjectOfferingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_subject_offering_endpoint(
    payload: SubjectOfferingCreateRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> SubjectOfferingResponse:
    offering, teacher_ids = academic_service.create_subject_offering(
        db,
        school_id=school_auth.school.id,
        payload=payload,
        actor_user_id=school_auth.user.id,
    )
    return _to_offering_response(offering, teacher_ids)


@router.get("/subject-offerings", response_model=PaginatedResponse[SubjectOfferingResponse])
def list_subject_offerings_endpoint(
    class_group_id: uuid.UUID | None = Query(default=None),
    subject_id: uuid.UUID | None = Query(default=None),
    term_id: uuid.UUID | None = Query(default=None),
    offering_status: str | None = Query(default=None, alias="status"),
    pagination: PaginationParams = Depends(get_pagination_params),
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> PaginatedResponse[SubjectOfferingResponse]:
    offerings, total = academic_repo.list_subject_offerings(
        db,
        school_id=school_auth.school.id,
        class_group_id=class_group_id,
        subject_id=subject_id,
        term_id=term_id,
        status=offering_status,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    items = [
        _to_offering_response(
            offering,
            academic_repo.list_offering_teacher_ids(
                db, school_id=school_auth.school.id, subject_offering_id=offering.id
            ),
        )
        for offering in offerings
    ]
    return build_paginated_response(items, total=total, pagination=pagination)


@router.patch(
    "/subject-offerings/{offering_id}",
    response_model=SubjectOfferingResponse,
)
def update_subject_offering_endpoint(
    offering_id: uuid.UUID,
    payload: SubjectOfferingUpdateRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> SubjectOfferingResponse:
    offering, teacher_ids = academic_service.update_subject_offering(
        db,
        school_id=school_auth.school.id,
        offering_id=offering_id,
        payload=payload,
        actor_user_id=school_auth.user.id,
    )
    return _to_offering_response(offering, teacher_ids)


@router.post(
    "/subject-offerings/{offering_id}/teachers",
    response_model=SubjectOfferingResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_offering_teacher_endpoint(
    offering_id: uuid.UUID,
    payload: OfferingTeacherAssignRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> SubjectOfferingResponse:
    offering, teacher_ids = academic_service.assign_teacher_to_offering(
        db,
        school_id=school_auth.school.id,
        offering_id=offering_id,
        teacher_user_id=payload.teacher_user_id,
        actor_user_id=school_auth.user.id,
    )
    return _to_offering_response(offering, teacher_ids)


# --- Enrollments (SCH-04) ---
@router.post(
    "/enrollments",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_enrollment_endpoint(
    payload: EnrollmentCreateRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> EnrollmentResponse:
    enrollment = academic_service.create_enrollment(
        db,
        school_id=school_auth.school.id,
        payload=payload,
        actor_user_id=school_auth.user.id,
    )
    return EnrollmentResponse.model_validate(enrollment)


@router.get("/enrollments", response_model=PaginatedResponse[EnrollmentResponse])
def list_enrollments_endpoint(
    student_user_id: uuid.UUID | None = Query(default=None),
    class_group_id: uuid.UUID | None = Query(default=None),
    academic_year_id: uuid.UUID | None = Query(default=None),
    enrollment_status: str | None = Query(default=None, alias="status"),
    pagination: PaginationParams = Depends(get_pagination_params),
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> PaginatedResponse[EnrollmentResponse]:
    rows, total = academic_repo.list_enrollments(
        db,
        school_id=school_auth.school.id,
        student_user_id=student_user_id,
        class_group_id=class_group_id,
        academic_year_id=academic_year_id,
        status=enrollment_status,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [EnrollmentResponse.model_validate(r) for r in rows],
        total=total,
        pagination=pagination,
    )


@router.post(
    "/enrollments/{enrollment_id}/transfer",
    response_model=EnrollmentTransferResponse,
)
def transfer_enrollment_endpoint(
    enrollment_id: uuid.UUID,
    payload: EnrollmentTransferRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> EnrollmentTransferResponse:
    previous, new = academic_service.transfer_enrollment(
        db,
        school_id=school_auth.school.id,
        enrollment_id=enrollment_id,
        payload=payload,
        actor_user_id=school_auth.user.id,
    )
    return EnrollmentTransferResponse(
        previous_enrollment=EnrollmentResponse.model_validate(previous),
        new_enrollment=EnrollmentResponse.model_validate(new),
    )


@router.post(
    "/enrollments/{enrollment_id}/withdraw",
    response_model=EnrollmentResponse,
)
def withdraw_enrollment_endpoint(
    enrollment_id: uuid.UUID,
    payload: EnrollmentWithdrawRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> EnrollmentResponse:
    enrollment = academic_service.withdraw_enrollment(
        db,
        school_id=school_auth.school.id,
        enrollment_id=enrollment_id,
        payload=payload,
        actor_user_id=school_auth.user.id,
    )
    return EnrollmentResponse.model_validate(enrollment)
