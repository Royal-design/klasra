# API_SPECIFICATION.md — School LMS Backend API

This document specifies the HTTP API exposed by `backend/` for the planned Next.js frontend and other authorized clients.

## 1. General Conventions

- **Base path:** `/api/v1`
- **Content type:** `application/json` (except `multipart/form-data` for spreadsheet imports and file uploads, and binary streaming for authorized file downloads).
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

---

## 3. Planned Endpoints (By Slice)

> Endpoints below are **not yet implemented**. Exact payloads and query parameters will be finalized as each slice is built.

### Slice 4 — Student Self-Registration (`AUTH-02`, `AUTH-06`)

| Method | Path | Access | Description |
| --- | --- | --- | --- |
| `POST` | `/api/v1/registrations/students` | Public | Submit pending student account + school registration code |
| `GET` | `/api/v1/schools/{school_id}/registrations/students` | School Admin | List pending student registration requests |
| `POST` | `/api/v1/schools/{school_id}/registrations/students/{request_id}/approve` | School Admin | Approve and match student to enrollment (audited) |
| `POST` | `/api/v1/schools/{school_id}/registrations/students/{request_id}/reject` | School Admin | Reject registration request (audited) |

### Slice 5 — Parent/Guardian Linking (`AUTH-04`, `AUTH-06`)

| Method | Path | Access | Description |
| --- | --- | --- | --- |
| `POST` | `/api/v1/schools/{school_id}/guardian-links/invite` | School Admin | Create parent link record and send invite |
| `POST` | `/api/v1/guardian-links/verify` | Public / Parent | Verify contact token and link to parent account (pending approval) |
| `POST` | `/api/v1/schools/{school_id}/guardian-links/{link_id}/approve` | School Admin | Approve parent/student link (audited) |
| `POST` | `/api/v1/schools/{school_id}/guardian-links/{link_id}/revoke` | School Admin | Revoke parent/student link (audited) |
| `GET` | `/api/v1/parent/children` | Parent | List approved linked children across all schools |

### Slice 6 — Lessons & File Storage (`LEARN-01`)

| Method | Path | Access | Description |
| --- | --- | --- | --- |
| `POST` / `PATCH` | `/api/v1/offerings/{offering_id}/lessons` | Assigned Teacher | Create/publish/update lessons and materials |
| `GET` | `/api/v1/offerings/{offering_id}/lessons` | Assigned Teacher, Enrolled Student | List lessons for an offering |
| `GET` | `/api/v1/files/{file_id}/download` | Authorized Users | Stream authorized file with `Content-Disposition: attachment` |

### Slice 7 — Assignments & Submissions (`ASSIGN-01`..`ASSIGN-03`)

| Method | Path | Access | Description |
| --- | --- | --- | --- |
| `POST` / `PATCH` | `/api/v1/offerings/{offering_id}/assignments` | Assigned Teacher | Create/update assignments |
| `GET` | `/api/v1/offerings/{offering_id}/assignments` | Assigned Teacher, Enrolled Student | List assignments |
| `POST` | `/api/v1/assignments/{assignment_id}/submissions` | Enrolled Student | Submit text and/or allowed files (tracks history) |
| `GET` | `/api/v1/assignments/{assignment_id}/submissions` | Assigned Teacher, Enrolled Student (own) | View submissions |

### Slice 8 — Grades, Feedback & Progress (`ASSIGN-04`, `PROG-01`, `PROG-02`)

| Method | Path | Access | Description |
| --- | --- | --- | --- |
| `PUT` | `/api/v1/submissions/{submission_id}/grade` | Assigned Teacher | Record/update grade and feedback (audited) |
| `GET` | `/api/v1/students/me/progress` | Student | View own grades, feedback, and attendance |
| `GET` | `/api/v1/parent/children/{student_id}/progress` | Approved Parent | View approved child's grades, feedback, and attendance only |

### Slice 9 — Attendance (`ATT-01`, `ATT-02`)

| Method | Path | Access | Description |
| --- | --- | --- | --- |
| `PUT` | `/api/v1/offerings/{offering_id}/attendance` | Assigned Teacher | Record/update attendance for a date (attributed + timestamped) |
| `GET` | `/api/v1/offerings/{offering_id}/attendance` | Assigned Teacher, School Admin | View class attendance records |
| `GET` | `/api/v1/students/me/attendance` | Student | View own attendance history |
| `GET` | `/api/v1/parent/children/{student_id}/attendance` | Approved Parent | View approved child's attendance history |
