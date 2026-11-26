# IMPLEMENTATION_STATUS.md — Build Progress Tracker

**Last updated:** 26 November 2026  
**Active branch:** `master`  
**Latest verified commit:** `2668334` (`chore: initialize FastAPI backend foundation (Slice 1)`)

## 1. Slice Progress

| Slice | Scope | Requirement IDs | Status | Notes |
| --- | --- | --- | --- | --- |
| **1** | FastAPI foundation, config, PostgreSQL SQLAlchemy, Alembic, `/api/v1/health` | Foundation | **Done** | 3/3 `pytest` tests passing; live PostgreSQL (`lms`) verified `200 OK`; Alembic `1.20.1` configured |
| **2** | Schools, accounts, auth, memberships, roles, school-scoped authorization | `SCH-01`, `AUTH-01`, `AUTH-03`, `AUTH-05`, `AUTH-06` | **Done** | 7/7 `pytest` tests passing; migration `0001_slice2_auth_schools` applied to PostgreSQL `lms` |
| **3** | Academic years, terms, class groups, subjects, offerings, enrollments, spreadsheet import | `SCH-02`, `SCH-03`, `SCH-04`, `SCH-05` | **Done** | 9/9 `pytest` tests passing; migration `0002_slice3_academic_structure` applied to PostgreSQL `lms` |
| **4** | Student self-registration requests & admin approval | `AUTH-02`, `AUTH-06` | **Done** | 15/15 `pytest` tests passing; migration `0004_slice4_student_registration` applied to PostgreSQL `lms` |
| **5** | Parent invitations, verification, approval & multi-school child links (+ staff email activation) | `AUTH-04`, `AUTH-06` | **Done** | 18/18 `pytest` tests passing; migrations `0005_staff_invitations` & `0006_slice5_guardian_links` applied to PostgreSQL `lms` |
| **6** | Lessons & secure file storage | `LEARN-01` | **Done** | 19/19 `pytest` tests passing; migration `0007_slice6_lessons_and_files` applied to PostgreSQL `lms` |
| **7** | Assignments, text/file submissions & resubmission rules | `ASSIGN-01`, `ASSIGN-02`, `ASSIGN-03` | **Done** | 20/20 `pytest` tests passing; migration `0008_slice7_assignments` applied to PostgreSQL `lms` |
| **8** | Grades, feedback & student/parent progress views | `ASSIGN-04`, `PROG-01`, `PROG-02` | **Done** | 21/21 `pytest` tests passing; migration `0009_slice8_grades` applied to PostgreSQL `lms` |
| **9** | Attendance recording & history | `ATT-01`, `ATT-02`, `PROG-01`, `PROG-02` | Not Started | Next up (confirm Open Decision #6: attendance statuses) |
| **10** | Deployment, backups, monitoring & privacy review | Security & Ops | Not Started | Blocked on Open Decisions #1, #9 |

## 2. Requirement ID Coverage

| Requirement ID | Description | Status | Slice |
| --- | --- | --- | --- |
| `SCH-01` | Platform admin creates and manages schools | **Done** | 2 |
| `SCH-02` | School admin manages academic years and terms | **Done** | 3 |
| `SCH-03` | School admin configures year levels, class groups, subjects, teacher assignments | **Done** | 3 |
| `SCH-04` | School admin enrolls, transfers, withdraws students preserving history | **Done** | 3 |
| `SCH-05` | School admin imports students/staff from spreadsheet with validation | **Done** | 3 |
| `AUTH-01` | School admin creates accounts and assigns roles within their school | **Done** | 2 |
| `AUTH-02` | Student self-registration remains pending until school admin approval | **Done** | 4 |
| `AUTH-03` | Teacher associated with only one school | **Done** | 2 |
| `AUTH-04` | Parent account linked to multiple students across multiple schools | **Done** | 5 |
| `AUTH-05` | Every protected operation checks role and school/resource assignment | **Done** (Slices 2–5 scope; extends per slice) | 2 |
| `AUTH-06` | Audit trail for admin decisions, role, enrollment, and guardian link changes | **Done** (extends to grades/attendance in Slices 8–9) | 2–5 |
| `LEARN-01` | Teacher publishes lessons/materials to assigned subject offerings | **Done** | 6 |
| `ASSIGN-01` | Teacher creates assignment for assigned subject offering | **Done** | 7 |
| `ASSIGN-02` | Enrolled students submit typed text and file uploads | **Done** | 7 |
| `ASSIGN-03` | System records submission time and retains resubmission history | **Done** | 7 |
| `ASSIGN-04` | Teacher reviews submissions and records grade and feedback | **Done** | 8 |
| `PROG-01` | Student views only their own grades, attendance, and feedback | **In Progress** (grades & feedback done; attendance in Slice 9) | 8–9 |
| `PROG-02` | Approved parent views only linked children's grades, attendance, and feedback | **In Progress** (grades & feedback done; attendance in Slice 9) | 8–9 |
| `ATT-01` | Teacher records attendance for assigned offerings/classes | Not Started | 9 |
| `ATT-02` | Attendance changes include responsible user and timestamp | Not Started | 9 |

## 3. Completed Work Log

### Slice 1 — FastAPI Backend Foundation
- Initialized Git repository (`master` branch) and `.gitignore`.
- Created `backend/` with `pyproject.toml`, `.env.example`, and local virtual environment (`backend/.venv`).
- Implemented `app/core/config.py` (`pydantic-settings`, strict `CORS_ORIGINS`, required `DATABASE_URL`).
- Implemented synchronous SQLAlchemy 2.0 setup (`app/db/base.py`, `app/db/session.py`) and Alembic (`alembic.ini`, `alembic/env.py`).
- Implemented `app/main.py` with CORS and security headers, plus `GET /api/v1/health`.
- Verified with `pytest -v` (3 passed) and `alembic --version`.

### Slice 2 — Schools, Accounts, Auth & School-Scoped Authorization
- Added `argon2-cffi` (Argon2id password hashing) and `email-validator`.
- Added SQLAlchemy models (`schools`, `users`, `school_memberships`, `user_sessions`, `audit_events`) with PostgreSQL/SQLite partial unique index enforcing `AUTH-03` (at most one active school per teacher).
- Created and applied Alembic migration `0001_slice2_auth_schools` to local PostgreSQL `lms`.
- Implemented `HttpOnly` cookie sessions (`__Host-lms_session` when `COOKIE_SECURE=true`), CSRF validation (`X-CSRF-Token`), sliding-window IP rate limiting (`429`), and standard error envelope (`app/core/errors.py`).
- Implemented `/api/v1/auth/*`, `/api/v1/schools/*`, and `/api/v1/schools/{school_id}/users|memberships/*` endpoints with fail-closed school isolation, last-admin protection, session invalidation on logout/revocation, and audit logging.
- Added CLI bootstrap (`python -m app.cli create-platform-admin`).
- Verified with `pytest -v` (7 passed).

### Slice 2b — Password Recovery, Resend Email Adapter & Swagger CSRF Authorize
- Added `APIKeyHeader(name="X-CSRF-Token")` OpenAPI security scheme so Swagger UI (`/docs`) displays an **Authorize** button for write requests.
- Implemented `app/services/email.py` (`ResendEmailProvider`, `ConsoleEmailProvider`, `InMemoryEmailProvider`) with fail-fast config validation when `EMAIL_PROVIDER=resend`.
- Added `password_reset_tokens` model, repository, and Alembic migration `0003_password_reset_tokens`.
- Implemented `POST /api/v1/auth/forgot-password`, `POST /api/v1/auth/reset-password`, and `POST /api/v1/auth/change-password` with strict rate limiting, single-use hashed tokens, session invalidation, and audit logging.

### Slice 3 — Academic Structure, Enrollments & Bulk Import
- Added `terminology_config` on `schools` and 8 school-scoped models (`academic_years`, `terms`, `year_levels`, `class_groups`, `subjects`, `subject_offerings`, `offering_teachers`, `enrollments`).
- Created and applied Alembic migration `0002_slice3_academic_structure` to PostgreSQL `lms`.
- Implemented `app/repositories/academic_repo.py`, `app/services/academic.py`, `app/services/imports.py`, and routers `app/api/v1/academic.py` & `app/api/v1/imports.py`.
- Implemented history-preserving student enrollment, transfer, and withdrawal (`SCH-04`) with audit events.
- Implemented secure CSV & XLSX bulk import (`SCH-05`) with 5 MB limit, magic-byte check, `defusedxml`-protected `openpyxl` parsing, dry-run validation, and atomic commit.
- Verified with `pytest -v` (9 passed).

### Slice 4 — Student Self-Registration & Admin Approval
- Added `student_invites` (supporting both short-lived cohort registration codes and single-use email invitations) and `student_registration_requests` models, repository (`app/repositories/registration_repo.py`), and migration `0004_slice4_student_registration`.
- Implemented `POST /api/v1/registrations/students` (strict rate-limited, always assigns `student` + `pending`, verifies hashed expiring tokens/codes and invitation email binding).
- Implemented School Admin code generation, email invitation (via Resend), listing, approval (with optional class group enrollment + approval email), and rejection (revoking membership & sessions + rejection email), all audited.
- Verified with `pytest -v` (15 passed).

### Slice 5 + Staff Invitations — Teacher Email Activation & Multi-School Guardian Linking
- Added `staff_invitations` model, repository, service, router, and migration `0005_staff_invitations` so School Admins can invite teachers/admins by email to set their own password securely (enforcing `AUTH-03` single active school for teachers).
- Added `guardian_links` model, repository, service, router, and migration `0006_slice5_guardian_links` implementing invite → email token verification (`pending_approval`) → School Admin approval/revocation → multi-school `GET /api/v1/parent/children` (`AUTH-04`, `AUTH-06`).
- Verified with `pytest -v` (18 passed).

### Slice 6 — Lessons & Secure File Storage
- Added `lessons` and `stored_files` models, `app/repositories/lesson_repo.py`, `app/services/file_storage.py`, `app/services/lesson.py`, `app/api/v1/lessons.py`, and migration `0007_slice6_lessons_and_files`.
- Enforced allow-listed extensions (`.pdf`, `.png`, `.jpg`, `.jpeg`, `.txt`, `.docx`, `.pptx`), magic-byte validation, ZIP traversal checks, 10 MB size limit, random UUID filenames stored outside public web paths, and authorized download streaming (`Content-Disposition: attachment`, `X-Content-Type-Options: nosniff`).
- Verified with `pytest -v` (19 passed).

### Slice 7 — Assignments, Submissions & Resubmission History
- Added `assignments` and `submissions` models, extended `stored_files` with `assignment_id` & `submission_id`, created `app/repositories/assignment_repo.py`, `app/services/assignment.py`, `app/api/v1/assignments.py`, and migration `0008_slice7_assignments`.
- Enforced per-assignment `allow_late_submissions` (`409 LATE_SUBMISSION_NOT_ALLOWED`) and `allow_resubmissions` (`409 RESUBMISSION_NOT_ALLOWED`) policies, versioned submission history (`version_number`, `is_latest`), and strict student-to-student privacy on submissions and file downloads.
- Verified with `pytest -v` (20 passed).

### Slice 8 — Grades, Teacher Feedback & Student/Parent Progress Views
- Added `grades` model, `app/repositories/grade_repo.py`, `app/schemas/grade.py`, `app/services/grade.py`, `app/api/v1/grades.py`, and migration `0009_slice8_grades`.
- Implemented `PUT /api/v1/submissions/{id}/grade` (score bounds validation, `is_published` draft/publish visibility, audit logging on every create/update), `GET /api/v1/assignments/{id}/grades`, `GET /api/v1/students/me/grades` (`PROG-01`), and `GET /api/v1/parent/children/{id}/grades` (`PROG-02`).
- Verified with `pytest -v` (21 passed).

## 4. Next Up — Slice 9 Checklist

Before starting Slice 9 (Attendance & Attribution History — `ATT-01`, `ATT-02`, `PROG-01`, `PROG-02`):
- Confirm Open Decision #6: required attendance statuses (recommended default: `present`, `absent`, `late`, `excused`, with responsible user + timestamp attribution and full audit trail on changes).
