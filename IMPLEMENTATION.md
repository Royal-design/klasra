# IMPLEMENTATION.md — Technical Architecture & Build Plan

This document translates [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md) into a concrete backend architecture and 10-slice implementation plan.

## 1. Confirmed Technical Decisions

| Area | Decision | Notes |
| --- | --- | --- |
| Backend framework | FastAPI (Python 3.13+) | Lives in `backend/`, versioned under `/api/v1` |
| Frontend (later) | Next.js | Will live in `frontend/` as a separate client |
| Database | PostgreSQL (local for dev) | Synchronous SQLAlchemy 2.0 + `psycopg` v3 |
| Migrations | Alembic | Wired to `app.core.config` and `app.db.base.Base` |
| Environment | Standard Python `venv` + `pip` | Managed via `backend/pyproject.toml` |
| Version control | Git (`master` branch) | Remote: `https://github.com/Royal-design/lms` |

## 2. Backend Architecture

### Current Structure (Slice 1)

```text
backend/
├── pyproject.toml
├── .env.example
├── alembic.ini
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── app/
│   ├── main.py              # App factory, CORS, security headers, router mount
│   ├── core/
│   │   └── config.py        # pydantic-settings configuration
│   ├── db/
│   │   ├── base.py          # DeclarativeBase + deterministic constraint naming
│   │   └── session.py       # Engine, sessionmaker, get_db() dependency
│   └── api/
│       └── v1/
│           ├── router.py    # Combines v1 routers
│           └── health.py    # GET /api/v1/health
└── tests/
    └── test_health.py
```

### Target Structure (Slices 2–9)

As domain slices are added, keep layers cleanly separated inside `backend/app/`:

- `app/models/` — SQLAlchemy ORM models (one module per domain area, imported in `app/db/models.py` for Alembic autogenerate).
- `app/schemas/` — Pydantic request/response schemas (strict input validation, explicit response models so internal fields never leak).
- `app/services/` — Business logic, transaction boundaries, and audit event recording.
- `app/core/security.py` — Password hashing, token/session handling, and cryptographic helpers.
- `app/api/deps.py` — Reusable FastAPI dependencies for authentication, role checks, and school/resource authorization.
- `app/api/v1/` — Thin route handlers delegating to services.

## 3. Multi-Tenancy & Identity Model

To satisfy both strict school isolation and multi-school parent access:

1. **Identity is global (`users`):** One login account per person (email/phone, password hash, account status).
2. **School access is explicit (`school_memberships`):** Links a `user_id` to a `school_id` with a `role` (`school_admin`, `teacher`, `student`) and `status` (`pending`, `active`, `revoked`).
   - Database constraint enforces at most **one active school membership** for a `teacher` (`AUTH-03`).
   - Platform administrators are flagged separately (`is_platform_admin`) and do not automatically receive school-level read access to student learning data.
3. **Parent/guardian links (`guardian_links`):** Links a parent `user_id` to a student record (`student_id`, `school_id`) with `status` (`pending`, `approved`, `revoked`) and approval metadata (`AUTH-04`).
4. **Request authorization flow:**
   - Authenticate user → resolve active role/membership for the target `school_id` (or approved `guardian_link` for parent endpoints) → verify resource ownership/assignment before reading or mutating data.

## 4. Vertical Slice Roadmap

### Slice 1 — FastAPI Foundation *(Done)*
- **Scope:** Project scaffold, config, PostgreSQL SQLAlchemy setup, Alembic, security headers, CORS, `GET /api/v1/health`, and automated tests.

### Slice 2 — Schools, Accounts, Auth & School-Scoped Authorization
- **Requirements:** `SCH-01`, `AUTH-01`, `AUTH-03`, `AUTH-05`, `AUTH-06`
- **Tables:** `schools`, `users`, `school_memberships`, `audit_events` (plus session/refresh token store if using stateful sessions).
- **Key deliverables:** Platform admin school management, user creation/login/logout, school role assignment, teacher single-school constraint, school-scoped authorization dependencies, rate limiting, and audit logging.

### Slice 3 — Academic Structure, Enrollments & Bulk Import
- **Requirements:** `SCH-02`, `SCH-03`, `SCH-04`, `SCH-05`
- **Tables:** `academic_years`, `terms`, `year_levels`, `class_groups`, `subjects`, `subject_offerings`, `offering_teachers`, `enrollments`.
- **Key deliverables:** CRUD for school academic hierarchy, enrollment/transfer/withdrawal preserving history (effective dates + status), CSV/XLSX dry-run validation + commit import for students and staff.

### Slice 4 — Student Self-Registration & Approval
- **Requirements:** `AUTH-02`, `AUTH-06`
- **Tables:** `registration_codes` / `invitations`, `student_registration_requests`.
- **Key deliverables:** Student registration with school-issued code/invitation (pending state, zero school data access), school admin review/approve/reject workflow with enrollment matching and audit log.

### Slice 5 — Parent Invitations, Verification & Multi-School Links
- **Requirements:** `AUTH-04`, `AUTH-06`, `PROG-02` (link foundation)
- **Tables:** `guardian_links`, `verification_tokens` (hashed, expiring, single-use).
- **Key deliverables:** School-initiated parent invite, contact verification, admin approval/revocation, multi-school child listing for a single parent account, full audit trail.

### Slice 6 — Lessons & Secure File Storage
- **Requirements:** `LEARN-01`
- **Tables:** `lessons`, `lesson_attachments` / `stored_files`.
- **Key deliverables:** Teacher lesson publishing for assigned subject offerings, student read access for enrolled offerings, secure file upload/download (allow-list, size limit, UUID storage outside web root, authorized download streaming).

### Slice 7 — Assignments, Submissions & Resubmission Rules
- **Requirements:** `ASSIGN-01`, `ASSIGN-02`, `ASSIGN-03`
- **Tables:** `assignments`, `assignment_attachments`, `submissions`, `submission_files`.
- **Key deliverables:** Teacher assignment creation, student text + file submissions, timestamping, late/resubmission policy enforcement, and submission version history.

### Slice 8 — Grades, Feedback & Student/Parent Progress Views
- **Requirements:** `ASSIGN-04`, `PROG-01`, `PROG-02`
- **Tables:** `grades` (with publish status/history as decided), `audit_events` integration.
- **Key deliverables:** Teacher grading and feedback on submissions, student self-view, and parent view strictly scoped to approved linked children's grades, attendance, and feedback.

### Slice 9 — Attendance & History
- **Requirements:** `ATT-01`, `ATT-02`, `PROG-01`, `PROG-02`
- **Tables:** `attendance_records`, `attendance_history` (or audit trail with responsible user + timestamp).
- **Key deliverables:** Teacher attendance entry per assigned class/subject offering and date, edit attribution, student and approved parent attendance history views.

### Slice 10 — Deployment, Backups, Monitoring & Privacy Review
- **Scope:** Production hardening (TLS/mTLS for PostgreSQL, secrets management, automated encrypted backups, structured PII-safe logging, retention/deletion rules, and NDPA 2023 / local privacy review).

## 5. Open Decisions Mapped to Blocking Slices

These items from Section 10 of `PRODUCT_REQUIREMENTS.md` should be finalized before starting the slice that depends on them:

| # | Decision | Needed Before |
| --- | --- | --- |
| 1 | Initial operating country/countries & privacy compliance scope | Slice 10 (confirm early for data fields) |
| 2 | Student onboarding: invitation, short-lived registration code, or both | Slice 4 |
| 3 | Configurable class/year terminology & grading scales per school | Slice 3 & Slice 8 |
| 4 | Late submission & resubmission rules (school-level vs per-assignment) | Slice 7 |
| 5 | Allowed submission file types and max upload size | Slice 6 / Slice 7 |
| 6 | Required attendance statuses (e.g., present, absent, late, excused) | Slice 9 |
| 7 | Whether grades stay hidden until explicitly published by a teacher | Slice 8 |
| 8 | Notification channels (email, SMS, in-app) for invites/updates | Slice 4 & Slice 5 |
| 9 | Hosting, backup cadence, expected user volume, and availability targets | Slice 10 |
