# IMPLEMENTATION_STATUS.md — Build Progress Tracker

**Last updated:** 25 November 2026  
**Active branch:** `master`  
**Latest verified commit:** `2668334` (`chore: initialize FastAPI backend foundation (Slice 1)`)

## 1. Slice Progress

| Slice | Scope | Requirement IDs | Status | Notes |
| --- | --- | --- | --- | --- |
| **1** | FastAPI foundation, config, PostgreSQL SQLAlchemy, Alembic, `/api/v1/health` | Foundation | **Done** | 3/3 `pytest` tests passing; Alembic `1.20.1` configured |
| **2** | Schools, accounts, auth, memberships, roles, school-scoped authorization | `SCH-01`, `AUTH-01`, `AUTH-03`, `AUTH-05`, `AUTH-06` | Not Started | Next up |
| **3** | Academic years, terms, class groups, subjects, offerings, enrollments, spreadsheet import | `SCH-02`, `SCH-03`, `SCH-04`, `SCH-05` | Not Started | — |
| **4** | Student self-registration requests & admin approval | `AUTH-02`, `AUTH-06` | Not Started | Blocked on Open Decision #2 |
| **5** | Parent invitations, verification, approval & multi-school child links | `AUTH-04`, `AUTH-06` | Not Started | Blocked on Open Decision #8 |
| **6** | Lessons & secure file storage | `LEARN-01` | Not Started | Blocked on Open Decision #5 |
| **7** | Assignments, text/file submissions & resubmission rules | `ASSIGN-01`, `ASSIGN-02`, `ASSIGN-03` | Not Started | Blocked on Open Decisions #4, #5 |
| **8** | Grades, feedback & student/parent progress views | `ASSIGN-04`, `PROG-01`, `PROG-02` | Not Started | Blocked on Open Decisions #3, #7 |
| **9** | Attendance recording & history | `ATT-01`, `ATT-02`, `PROG-01`, `PROG-02` | Not Started | Blocked on Open Decision #6 |
| **10** | Deployment, backups, monitoring & privacy review | Security & Ops | Not Started | Blocked on Open Decisions #1, #9 |

## 2. Requirement ID Coverage

| Requirement ID | Description | Status | Slice |
| --- | --- | --- | --- |
| `SCH-01` | Platform admin creates and manages schools | Not Started | 2 |
| `SCH-02` | School admin manages academic years and terms | Not Started | 3 |
| `SCH-03` | School admin configures year levels, class groups, subjects, teacher assignments | Not Started | 3 |
| `SCH-04` | School admin enrolls, transfers, withdraws students preserving history | Not Started | 3 |
| `SCH-05` | School admin imports students/staff from spreadsheet with validation | Not Started | 3 |
| `AUTH-01` | School admin creates accounts and assigns roles within their school | Not Started | 2 |
| `AUTH-02` | Student self-registration remains pending until school admin approval | Not Started | 4 |
| `AUTH-03` | Teacher associated with only one school | Not Started | 2 |
| `AUTH-04` | Parent account linked to multiple students across multiple schools | Not Started | 5 |
| `AUTH-05` | Every protected operation checks role and school/resource assignment | Not Started | 2 |
| `AUTH-06` | Audit trail for admin decisions, role, enrollment, and guardian link changes | Not Started | 2–5 |
| `LEARN-01` | Teacher publishes lessons/materials to assigned subject offerings | Not Started | 6 |
| `ASSIGN-01` | Teacher creates assignment for assigned subject offering | Not Started | 7 |
| `ASSIGN-02` | Enrolled students submit typed text and file uploads | Not Started | 7 |
| `ASSIGN-03` | System records submission time and retains resubmission history | Not Started | 7 |
| `ASSIGN-04` | Teacher reviews submissions and records grade and feedback | Not Started | 8 |
| `PROG-01` | Student views only their own grades, attendance, and feedback | Not Started | 8–9 |
| `PROG-02` | Approved parent views only linked children's grades, attendance, and feedback | Not Started | 8–9 |
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

## 4. Next Up — Slice 2 Checklist

Before starting Slice 2, decide:
- **Auth mechanism for Next.js:** `HttpOnly` secure session cookies + CSRF token (recommended for browser security) vs. JWT Bearer tokens.
- **Initial Platform Admin bootstrap:** CLI/seed script vs. environment-seeded bootstrap command.

Once confirmed, Slice 2 will deliver `schools`, `users`, `school_memberships`, `audit_events`, authentication endpoints, school-scoped authorization dependencies, Alembic migration #1, and full authorization tests.
