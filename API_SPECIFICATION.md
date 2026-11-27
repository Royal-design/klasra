# API_SPECIFICATION.md — School LMS Backend API

This document specifies the HTTP API exposed by `backend/` for the planned Next.js frontend and other authorized clients.

## 1. General Conventions

- **Base path:** `/api/v1`
- **Content type:** `application/json` (except `multipart/form-data` for spreadsheet imports and file uploads, and binary streaming for authorized file downloads).
- **Pagination & filtering standard (all `GET` list endpoints):**
  - Query parameters: `page` (1-based, default `1`), `page_size` (default `20`, max `100`), plus resource-specific filters (`q` case-insensitive search, `status`, `role`, `academic_year_id`, `class_group_id`, `student_user_id`, etc.).
  - Envelope format:
    ```json
    {
      "items": [],
      "meta": {
        "total": 42,
        "page": 1,
        "page_size": 20,
        "total_pages": 3,
        "has_next": true,
        "has_prev": false
      }
    }
    ```
- **Interactive docs (non-production only):** `/docs` (Swagger UI) and `/openapi.json`. Disabled when `APP_ENV=production`.
- **CORS:** Restricted to explicit origins configured in `CORS_ORIGINS` (default `http://localhost:3000`). Wildcard `*` is rejected at startup.
- **Security headers (all `/api/v1/*` responses):**
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Permissions-Policy: camera=(), microphone=(), geolocation=()`
  - `Cache-Control: no-store`
  - `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'`
- **Error handling:** Errors return standard HTTP status codes (`400`, `401`, `403`, `404`, `409`, `410`, `413`, `415`, `422`, `429`, `500`, `503`) with generic, user-safe JSON messages. Internal SQL errors, connection strings, and stack traces are never returned.
- **Standard error response format (enforced starting Slice 2):**
  ```json
  {
    "error": {
      "code": "FORBIDDEN",
      "message": "You do not have permission to perform this action.",
      "details": []
    }
  }
  ```
  - `code`: Stable machine-readable string (e.g., `INVALID_CREDENTIALS`, `MEMBERSHIP_PENDING`, `TEACHER_SINGLE_SCHOOL_VIOLATION`, `LAST_SCHOOL_ADMIN`, `INVALID_STATE_TRANSITION`, `TOKEN_INVALID_OR_EXPIRED`, `RATE_LIMITED`, `VALIDATION_ERROR`, `SERVICE_UNAVAILABLE`).
  - `message`: Plain-language, safe-to-display explanation (never leaks whether another tenant's resource or another user's email exists).
  - `details`: Optional list of field-level validation issues (used on `422`).
- **Key edge-case HTTP mappings:**
  - `401 Unauthorized` — Missing, expired, or invalid credentials/session.
  - `403 Forbidden` — Authenticated user lacks role/school/resource permission, account is inactive, membership is pending, or CSRF validation failed.
  - `404 Not Found` — Resource does not exist (also used when hiding cross-school resource existence).
  - `409 Conflict` — Business-rule conflict (duplicate email/slug, teacher already active in another school, removing last school admin, invalid state transition, or destructive delete of historical records).
  - `410 Gone` — Single-use invitation or verification token has expired or already been consumed.
  - `422 Unprocessable Entity` — Schema/input validation error (bad UUID, missing field, invalid date range).
  - `429 Too Many Requests` — Rate limit exceeded (includes `Retry-After` header).
  - `503 Service Unavailable` — Database or critical dependency temporarily unreachable.
- **Authentication (Implemented in Slice 2):** Cookie-based server-side sessions (`__Host-lms_session` when `COOKIE_SECURE=true`, `lms_session` in local HTTP dev; `HttpOnly`, `SameSite=Lax`, `Path=/`, no `Domain`) paired with CSRF protection (`X-CSRF-Token` header verified against the session's stored CSRF token hash on all state-changing requests). All endpoints except `/api/v1/health` and `/api/v1/auth/login` require authentication and server-side role + school/resource authorization.

---

## 2. Implemented Endpoints

### Health

#### `GET /api/v1/health`
- **Status:** Implemented (Slice 1)
- **Auth:** Public (rate-limited)
- **Purpose:** Confirms the API process is running and can execute `SELECT 1` against PostgreSQL.
- **Responses:**
  - `200 OK`
    ```json
    {
      "status": "ok",
      "database": "ok"
    }
    ```
  - `503 Service Unavailable`
    ```json
    {
      "status": "degraded",
      "database": "unavailable"
    }
    ```

### Authentication (Slice 2 + Password Recovery)

| Method | Path | Access | CSRF Required | Description |
| --- | --- | --- | --- | --- |
| `POST` | `/api/v1/auth/login` | Public (strict rate limit) | No | Verify email & Argon2id password, set `HttpOnly` session cookie + CSRF cookie, return `user` + `csrf_token`. |
| `POST` | `/api/v1/auth/logout` | Authenticated | Yes | Invalidate all active sessions for the current user and clear cookies (`204 No Content`). |
| `GET` | `/api/v1/auth/me` | Authenticated | No | Return current user profile and school memberships. |
| `POST` | `/api/v1/auth/forgot-password` | Public (strict rate limit) | No | Always returns generic `200 OK` (no email enumeration). Creates a 30-minute single-use hashed token and emails a reset link via Resend (`EMAIL_PROVIDER=resend`). |
| `POST` | `/api/v1/auth/reset-password` | Public (strict rate limit) | No | Consumes single-use reset token (`410 Gone` if invalid/expired/used), updates Argon2id password, and revokes all active sessions (audited). |
| `POST` | `/api/v1/auth/change-password` | Authenticated | Yes | Verifies current password, updates Argon2id password, revokes all active sessions, and clears cookies (audited). |

> **Swagger UI (`/docs`) testing:** Run `POST /api/v1/auth/login` first (your browser automatically stores the session cookie when `COOKIE_SECURE=false` locally), then click **Authorize** and paste the `csrf_token` into `CSRFToken` (`X-CSRF-Token`).

### Schools — Platform Admin (Slice 2 — `SCH-01`, `AUTH-06`)

| Method | Path | Access | CSRF Required | Description |
| --- | --- | --- | --- | --- |
| `POST` | `/api/v1/schools` | Platform Admin | Yes | Create a school and its initial active `school_admin` account (audited). Returns `201 Created`. |
| `GET` | `/api/v1/schools` | Platform Admin | No | List all schools. |
| `PATCH` | `/api/v1/schools/{school_id}` | Platform Admin | Yes | Update school `name` or `status` (`active` / `suspended`) (audited). |

### School Users & Memberships — School Admin (Slice 2 — `AUTH-01`, `AUTH-03`, `AUTH-05`, `AUTH-06`)

| Method | Path | Access | CSRF Required | Description |
| --- | --- | --- | --- | --- |
| `POST` | `/api/v1/schools/{school_id}/users` | School Admin of `{school_id}` | Yes | Create a user (or attach existing user) with role `school_admin`, `teacher`, or `student` in `{school_id}`. Enforces `AUTH-03` single active school for teachers (`409 TEACHER_SINGLE_SCHOOL_VIOLATION`). Audited. |
| `GET` | `/api/v1/schools/{school_id}/users` | School Admin of `{school_id}` | No | List users and memberships strictly scoped to `{school_id}`. |
| `PATCH` | `/api/v1/schools/{school_id}/memberships/{membership_id}` | School Admin of `{school_id}` | Yes | Update role or status (`pending` / `active` / `revoked`). Prevents removing/demoting the last active `school_admin` (`409 LAST_SCHOOL_ADMIN`), enforces `AUTH-03`, invalidates user sessions on revocation, and records an audit event. |

### Academic Structure, Offerings & Enrollments — School Admin (Slice 3 — `SCH-02`, `SCH-03`, `SCH-04`)

All endpoints below require an active **`school_admin`** membership in `{school_id}` (+ `X-CSRF-Token` on `POST`/`PATCH`). Cross-school references fail closed (`403` / `404` / `422`).

| Method | Path | Description |
| --- | --- | --- |
| `POST` / `GET` / `PATCH` | `/api/v1/schools/{school_id}/academic-years` (`/{academic_year_id}`) | Create, list, and update academic years (`end_date > start_date`, unique name per school). |
| `POST` / `GET` / `PATCH` | `/api/v1/schools/{school_id}/terms` (`/{term_id}`) | Create, list (optional `?academic_year_id=`), and update terms (must fall inside academic year dates). |
| `POST` / `GET` / `PATCH` | `/api/v1/schools/{school_id}/year-levels` (`/{year_level_id}`) | Create, list, and update year levels/forms (`display_order`). |
| `POST` / `GET` / `PATCH` | `/api/v1/schools/{school_id}/class-groups` (`/{class_group_id}`) | Create, list (optional `?academic_year_id=`), and update class groups/sections. |
| `POST` / `GET` / `PATCH` | `/api/v1/schools/{school_id}/subjects` (`/{subject_id}`) | Create, list, and update subjects (unique uppercase `code` per school). |
| `POST` / `GET` / `PATCH` | `/api/v1/schools/{school_id}/subject-offerings` (`/{offering_id}`) | Create, list (optional `?class_group_id=`), and update subject offerings with initial active teachers. |
| `POST` | `/api/v1/schools/{school_id}/subject-offerings/{offering_id}/teachers` | Assign an active school teacher to a subject offering (audited). |
| `POST` / `GET` | `/api/v1/schools/{school_id}/enrollments` | Enroll an active school student into a class group (and optional subject offering); list enrollments with filters (`student_user_id`, `class_group_id`, `status`). |
| `POST` | `/api/v1/schools/{school_id}/enrollments/{enrollment_id}/transfer` | Mark active enrollment `transferred` with `effective_to` and create a new `active` enrollment row (history preserved, audited). |
| `POST` | `/api/v1/schools/{school_id}/enrollments/{enrollment_id}/withdraw` | Mark active enrollment `withdrawn` with `effective_to` (history preserved, audited). |

### Bulk Spreadsheet Import — School Admin (Slice 3 — `SCH-05`)

Accepts `multipart/form-data` (`file`: `.csv` UTF-8 or `.xlsx` verified via `PK\x03\x04` magic bytes + `defusedxml`, max 5 MB). Required columns: `email`, `full_name`, `role` (`teacher` or `student`; admin roles rejected). Optional columns for students: `academic_year`, `class_group`.

| Method | Path | Access | CSRF Required | Description |
| --- | --- | --- | --- | --- |
| `POST` | `/api/v1/schools/{school_id}/imports/validate` | School Admin | Yes | Dry-run validate spreadsheet and return row-level errors + preview without writing to DB. |
| `POST` | `/api/v1/schools/{school_id}/imports/commit` | School Admin | Yes | Validate and atomically commit users, memberships, and optional student enrollments (audited). Rejects with `422 IMPORT_VALIDATION_FAILED` if any row has errors. |

### Student Self-Registration & Admin Approval (Slice 4 — `AUTH-02`, `AUTH-06`)

Registration codes and email invitations identify a school cohort or invited student email; they **never** grant immediate school access or elevated roles. Every self-registered student remains `pending` until approved by a School Admin.

| Method | Path | Access | CSRF Required | Description |
| --- | --- | --- | --- | --- |
| `POST` | `/api/v1/registrations/students` | Public (strict rate limit) | No | Submit a pending student self-registration with a valid registration code or single-use email invitation token. Always assigns `role=student`, `status=pending` (audited). |
| `POST` | `/api/v1/schools/{school_id}/registrations/codes` | School Admin | Yes | Generate a short-lived cohort registration code (returns raw `code` once; stores SHA-256 hash only; audited). |
| `POST` | `/api/v1/schools/{school_id}/registrations/invitations` | School Admin | Yes | Create a single-use email invitation bound to `invited_email` and send the registration link via Resend (audited). |
| `GET` | `/api/v1/schools/{school_id}/registrations/students` | School Admin | No | List student registration requests for `{school_id}` (optional `?status=pending\|approved\|rejected`). |
| `POST` | `/api/v1/schools/{school_id}/registrations/students/{request_id}/approve` | School Admin | Yes | Approve a pending student registration, activate membership, optionally enroll into `class_group_id`, notify via Resend, and record audit event. |
| `POST` | `/api/v1/schools/{school_id}/registrations/students/{request_id}/reject` | School Admin | Yes | Reject a pending registration, revoke membership & active sessions, notify via Resend, and record audit event. |

### Staff/Teacher Email Invitations & Self-Activation (Slice 4b — `AUTH-01`, `AUTH-03`, `AUTH-06`)

Teachers cannot self-register via open cohort codes. Instead, School Admins send single-use email invitations so staff can set their own passwords securely.

| Method | Path | Access | CSRF Required | Description |
| --- | --- | --- | --- | --- |
| `POST` | `/api/v1/schools/{school_id}/staff-invitations` | School Admin | Yes | Create a single-use hashed staff invitation (`teacher` or `school_admin`), enforce `AUTH-03`, email activation link via Resend (audited). |
| `GET` | `/api/v1/schools/{school_id}/staff-invitations` | School Admin | No | List staff invitations for `{school_id}` (paginated, `?q=`). |
| `POST` | `/api/v1/staff-invitations/accept` | Public (strict rate limit) | No | Accept single-use staff invitation, set password (or verify existing account password), activate school membership (audited). |

### Parent/Guardian Multi-School Linking (Slice 5 — `AUTH-04`, `AUTH-06`)

| Method | Path | Access | CSRF Required | Description |
| --- | --- | --- | --- | --- |
| `POST` | `/api/v1/schools/{school_id}/guardian-links/invite` | School Admin | Yes | Record parent-student link and email single-use verification token via Resend (audited). |
| `GET` | `/api/v1/schools/{school_id}/guardian-links` | School Admin | No | List guardian links for `{school_id}` (paginated, `?student_user_id=&status=&q=`). |
| `POST` | `/api/v1/guardian-links/verify` | Public (strict rate limit) | No | Verify email token, create or link to existing single parent account (requiring existing password if account exists), transition to `pending_approval` (audited). |
| `POST` | `/api/v1/schools/{school_id}/guardian-links/{link_id}/approve` | School Admin | Yes | Approve verified parent-student link and notify via Resend (audited). |
| `POST` | `/api/v1/schools/{school_id}/guardian-links/{link_id}/revoke` | School Admin | Yes | Revoke parent-student link immediately and notify via Resend (audited). |
| `GET` | `/api/v1/parent/children` | Authenticated Parent | No | List **only approved** linked children across all active schools (paginated, `?school_id=&q=`). |

### Lessons, Video Support & Secure File Storage (Slice 6 + Slice 10 — `LEARN-01`)

- **Document/Image attachments (10 MB max):** `.pdf`, `.png`, `.jpg`, `.jpeg`, `.txt`, `.docx`, `.pptx` with magic-byte validation and ZIP path-traversal checks.
- **Lesson Video attachments (50 MB max, teachers on lessons only — never student submissions):** `.mp4`, `.webm`, `.mov` with magic-byte validation (`ftyp`, WebM EBML, QuickTime atoms).
- **External Video Links (`video_url` on lessons):** Optional `https://` URL strictly allow-listed to YouTube, Vimeo, and Loom.
- **Storage & Direct Uploads:** Supports `STORAGE_PROVIDER=local` (dev/tests) and `STORAGE_PROVIDER=s3` (Backblaze B2 / Cloudflare R2 / AWS S3 / Supabase) with short-lived presigned PUT uploads and signed GET playback/download URLs.

| Method | Path | Access | CSRF Required | Description |
| --- | --- | --- | --- | --- |
| `POST` | `/api/v1/offerings/{offering_id}/lessons` | Assigned Teacher | Yes | Create a `draft` or `published` lesson (with optional allow-listed `video_url`) for an assigned subject offering (audited). |
| `GET` | `/api/v1/offerings/{offering_id}/lessons` | Assigned Teacher, Enrolled Student | No | List lessons (paginated, `?status=&q=`). Teachers see drafts + published; enrolled students see **published only**. |
| `PATCH` | `/api/v1/offerings/{offering_id}/lessons/{lesson_id}` | Assigned Teacher | Yes | Update lesson title, content, `video_url`, or publish status (audited). |
| `POST` | `/api/v1/offerings/{offering_id}/lessons/{lesson_id}/attachments` | Assigned Teacher | Yes | Upload an allow-listed learning material (≤10 MB) or lesson video (≤50 MB) via `multipart/form-data` (audited). |
| `POST` | `/api/v1/offerings/{offering_id}/lessons/{lesson_id}/attachments/presign` | Assigned Teacher | Yes | Request a short-lived S3 presigned PUT URL for direct browser upload to object storage (`STORAGE_PROVIDER=s3`). |
| `POST` | `/api/v1/offerings/{offering_id}/lessons/{lesson_id}/attachments/complete` | Assigned Teacher | Yes | Verify uploaded S3 object size & magic bytes and register it on the lesson (audited). |
| `GET` | `/api/v1/files/{file_id}/download` | Assigned Teacher, Enrolled Student | No | Stream authorized file attachment (students blocked from draft lesson files; parents/outsiders blocked `403`). |
| `GET` | `/api/v1/files/{file_id}/download-url` | Assigned Teacher, Enrolled Student | No | Return a short-lived signed download/playback URL (`?inline=true` for video/PDF players) on S3, or proxy path on local storage. |

### Assignments & Submissions (Slice 7 — `ASSIGN-01`, `ASSIGN-02`, `ASSIGN-03`)

| Method | Path | Access | CSRF Required | Description |
| --- | --- | --- | --- | --- |
| `POST` | `/api/v1/offerings/{offering_id}/assignments` | Assigned Teacher | Yes | Create a `draft` or `published` assignment with `due_at`, `max_score`, `allow_late_submissions`, and `allow_resubmissions` (audited). |
| `GET` | `/api/v1/offerings/{offering_id}/assignments` | Assigned Teacher, Enrolled Student | No | List assignments (paginated, `?status=&q=`). Students see **published only**. |
| `PATCH` | `/api/v1/offerings/{offering_id}/assignments/{assignment_id}` | Assigned Teacher | Yes | Update assignment instructions, policy, or publish status (audited). |
| `POST` | `/api/v1/offerings/{offering_id}/assignments/{assignment_id}/attachments` | Assigned Teacher | Yes | Upload an allow-listed attachment to an assignment (`multipart/form-data`, audited). |
| `POST` | `/api/v1/assignments/{assignment_id}/submissions` | Enrolled Student | Yes | Submit typed `text_content` and/or `files` (`multipart/form-data`). Enforces late/resubmission rules (`409`) and retains full `version_number` history (audited). |
| `GET` | `/api/v1/assignments/{assignment_id}/submissions` | Assigned Teacher, Enrolled Student (own) | No | List submissions (paginated, `?student_user_id=&latest_only=`). Students see **only their own** history. |

### Grades, Feedback & Progress Views (Slice 8 — `ASSIGN-04`, `PROG-01`, `PROG-02`)

| Method | Path | Access | CSRF Required | Description |
| --- | --- | --- | --- | --- |
| `PUT` | `/api/v1/submissions/{submission_id}/grade` | Assigned Teacher | Yes | Record or update `score` (`0 <= score <= max_score`), `letter_grade`, `feedback`, and `is_published` (audited on every create/change). |
| `GET` | `/api/v1/assignments/{assignment_id}/grades` | Assigned Teacher | No | List all grades (draft + published) for an assignment (paginated, `?is_published=`). |
| `GET` | `/api/v1/students/me/grades` | Student | No | View **only own published** grades and teacher feedback (paginated, `?subject_offering_id=&q=`). |
| `GET` | `/api/v1/parent/children/{student_id}/grades` | Approved Parent | No | View **only approved child's published** grades and teacher feedback (paginated, `?q=`; `403` for unapproved/revoked/other students). |

### Attendance & Attribution History (Slice 9 — `ATT-01`, `ATT-02`, `PROG-01`, `PROG-02`)

Allowed statuses: `present`, `absent`, `late`, `excused`. Every record and update stores `recorded_by_user_id`, `updated_by_user_id`, timestamps, and an immutable `audit_events` row.

| Method | Path | Access | CSRF Required | Description |
| --- | --- | --- | --- | --- |
| `PUT` | `/api/v1/offerings/{offering_id}/attendance` | Assigned Teacher | Yes | Batch record or update attendance for enrolled students on `attendance_date` (attributed + audited). |
| `GET` | `/api/v1/offerings/{offering_id}/attendance` | Assigned Teacher, School Admin | No | List offering attendance records (paginated, `?attendance_date=&student_user_id=&status=`). |
| `GET` | `/api/v1/students/me/attendance` | Student | No | View **only own** attendance history (paginated, `?subject_offering_id=&status=&date_from=&date_to=`). |
| `GET` | `/api/v1/parent/children/{student_id}/attendance` | Approved Parent | No | View **only approved child's** attendance history (paginated, `?status=&date_from=&date_to=`; `403` otherwise). |

### Quizzes, Tests (CA) & Exams (Slice 11 — `ASSESS-01`, `PROG-01`, `PROG-02`)

Supports `assessment_type` = `quiz` | `test` | `exam` with timed windows (`available_from`, `available_until`, `time_limit_minutes`), attempt limits (`max_attempts`), auto-graded objective questions (`single_choice`, `true_false`, `multi_select`), manually graded `short_answer` essays, and draft-to-publish score visibility. `correct_answers` are always stripped for students.

| Method | Path | Access | CSRF Required | Description |
| --- | --- | --- | --- | --- |
| `POST` | `/api/v1/offerings/{offering_id}/assessments` | Assigned Teacher | Yes | Create a `quiz`, `test`, or `exam` (audited). |
| `GET` | `/api/v1/offerings/{offering_id}/assessments` | Assigned Teacher, Enrolled Student | No | List assessments (paginated, `?assessment_type=&status=&q=`). Students see `published`/`closed` only with `correct_answers` hidden. |
| `PATCH` | `/api/v1/offerings/{offering_id}/assessments/{assessment_id}` | Assigned Teacher | Yes | Update settings, window, or publish/close status (audited). |
| `POST` | `/api/v1/offerings/{offering_id}/assessments/{assessment_id}/questions` | Assigned Teacher | Yes | Add `single_choice`, `true_false`, `multi_select`, or `short_answer` question and recalculate `total_points`. |
| `DELETE` | `/api/v1/offerings/{offering_id}/assessments/{assessment_id}/questions/{question_id}` | Assigned Teacher | Yes | Remove a question and recalculate `total_points`. |
| `POST` | `/api/v1/assessments/{assessment_id}/attempts` | Enrolled Student | Yes | Start or resume a timed attempt (enforces availability window & `max_attempts`, audited). |
| `POST` | `/api/v1/attempts/{attempt_id}/submit` | Student (owner) | Yes | Submit answers; auto-grades objective questions and optionally publishes immediately when `show_results_immediately=true` (audited). |
| `GET` | `/api/v1/assessments/{assessment_id}/attempts` | Assigned Teacher, Enrolled Student (own) | No | List attempts (paginated, `?student_user_id=&status=`). Students see only their own, with scores hidden until published. |
| `PUT` | `/api/v1/attempts/{attempt_id}/grade` | Assigned Teacher | Yes | Grade `short_answer` questions, set `teacher_feedback`, and publish/unpublish results (audited). |
| `GET` | `/api/v1/students/me/assessments` | Student | No | View **only own published** quiz/test/exam results (paginated, `?assessment_type=`). |
| `GET` | `/api/v1/parent/children/{student_id}/assessments` | Approved Parent | No | View **only approved child's published** quiz/test/exam results (paginated, `?assessment_type=`; `403` otherwise). |

---

## 3. Production Hardening & Observability (Slice 10)

All 10 backend slices are implemented! Production deployment, S3/Backblaze B2 object storage, encrypted PostgreSQL backup/restore procedures, structured JSON PII-safe logging (`X-Request-ID`), and NDPA 2023 privacy review are documented in [`DEPLOYMENT_AND_PRIVACY.md`](DEPLOYMENT_AND_PRIVACY.md).
