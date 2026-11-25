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
- **Error handling:** Errors return standard HTTP status codes (`400`, `401`, `403`, `404`, `409`, `422`, `429`, `503`) with generic user-safe JSON messages. Internal SQL errors and stack traces are never returned.
- **Authentication (Slice 2):** All endpoints except `/api/v1/health` and explicit auth/registration entry points will require authentication and server-side role + school/resource authorization.

---

## 2. Implemented Endpoints

### Health

#### `GET /api/v1/health`
- **Status:** Implemented (Slice 1)
- **Auth:** Public (liveness/readiness probe; rate limiting planned in Slice 2)
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

---

## 3. Planned Endpoints (By Slice)

> Endpoints below are **not yet implemented**. Exact payloads and query parameters will be finalized as each slice is built.

### Slice 2 — Auth, Schools & Memberships (`SCH-01`, `AUTH-01`, `AUTH-03`, `AUTH-05`, `AUTH-06`)

| Method | Path | Access | Description |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/login` | Public | Authenticate user and issue session/tokens |
| `POST` | `/api/v1/auth/logout` | Authenticated | Invalidate active session |
| `GET` | `/api/v1/auth/me` | Authenticated | Return current user profile and school memberships |
| `POST` | `/api/v1/schools` | Platform Admin | Create a school and initial school admin |
| `GET` | `/api/v1/schools` | Platform Admin | List schools |
| `PATCH` | `/api/v1/schools/{school_id}` | Platform Admin | Update school metadata/status |
| `POST` | `/api/v1/schools/{school_id}/users` | School Admin | Create user account and assign school role |
| `GET` | `/api/v1/schools/{school_id}/users` | School Admin | List users within the school |
| `PATCH` | `/api/v1/schools/{school_id}/memberships/{membership_id}` | School Admin | Update or revoke role/membership (audited) |

### Slice 3 — Academic Structure, Enrollments & Import (`SCH-02`..`SCH-05`)

| Method | Path | Access | Description |
| --- | --- | --- | --- |
| `POST` / `GET` / `PATCH` | `/api/v1/schools/{school_id}/academic-years` | School Admin | Manage academic years |
| `POST` / `GET` / `PATCH` | `/api/v1/schools/{school_id}/terms` | School Admin | Manage terms within an academic year |
| `POST` / `GET` / `PATCH` | `/api/v1/schools/{school_id}/year-levels` | School Admin | Manage year levels/forms |
| `POST` / `GET` / `PATCH` | `/api/v1/schools/{school_id}/class-groups` | School Admin | Manage class groups/sections |
| `POST` / `GET` / `PATCH` | `/api/v1/schools/{school_id}/subjects` | School Admin | Manage subjects |
| `POST` / `GET` / `PATCH` | `/api/v1/schools/{school_id}/subject-offerings` | School Admin | Assign subjects & teachers to class groups |
| `POST` / `GET` / `PATCH` | `/api/v1/schools/{school_id}/enrollments` | School Admin | Enroll, transfer, or withdraw students (history preserved) |
| `POST` | `/api/v1/schools/{school_id}/imports/validate` | School Admin | Dry-run spreadsheet validation and error report |
| `POST` | `/api/v1/schools/{school_id}/imports/commit` | School Admin | Commit validated student/staff import |

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
