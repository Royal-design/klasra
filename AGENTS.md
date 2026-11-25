# AGENTS.md — Working Guide for AI Coding Assistants

This file defines the rules, conventions, and workflow for any AI assistant (or developer) working on the **School LMS** repository.

## 1. Read First

Before proposing or making changes, read:

1. `PRODUCT_REQUIREMENTS.md` — source of truth for scope, user roles, requirement IDs, and open decisions.
2. `IMPLEMENTATION_STATUS.md` — current progress across the 10 build slices.
3. `IMPLEMENTATION.md` — technical architecture, database conventions, and slice breakdown.
4. `API_SPECIFICATION.md` — implemented and planned API contracts for the Next.js frontend.

## 2. Project Stack & Layout

- **Backend:** Python 3.13+, FastAPI, synchronous SQLAlchemy 2.0, Alembic, PostgreSQL (`psycopg` v3), `pydantic-settings`, `pytest`.
- **Frontend (planned):** Next.js in `frontend/` as a separate client consuming `/api/v1`.
- **Repository layout:**
  - `backend/` — FastAPI application, Alembic migrations, and automated tests.
  - `frontend/` — *(not yet created)* Next.js application.
  - Root markdown docs — requirements, architecture, API spec, and status tracker.

## 3. Slice-by-Slice Workflow Rules

Follow Section 11 of `PRODUCT_REQUIREMENTS.md` on every feature slice:

1. **Before editing:** State your assumptions, identify the requirement IDs in scope, and list the files you plan to create or modify.
2. **Stay in scope:** Implement only the selected slice and requirement IDs. Do not build future slices early.
3. **Migrations & tests:** Every schema change must include an Alembic migration. Every new behavior and authorization rule must have focused `pytest` tests.
4. **Explain authorization & edge cases:** Document which roles can call each endpoint, how school/resource scoping is enforced, and what happens on unauthorized or cross-school access.
5. **Keep docs in sync:** Update `API_SPECIFICATION.md` and `IMPLEMENTATION_STATUS.md` whenever endpoints, models, or slice statuses change.
6. **Self-review:** Check your diff against the slice acceptance criteria and report anything incomplete.

## 4. Non-Negotiable Security & Multi-Tenancy Rules

- **School data separation:** Every school-owned table must include `school_id`. Every query and mutation on school-owned records must filter by the authorized `school_id` and role/assignment.
- **API-enforced authorization:** Never rely on the frontend UI for access control. Enforce authentication, role checks, and resource ownership checks on the server for every protected endpoint (fail closed).
- **Role invariants:**
  - Platform administrators manage schools and platform operations, and do not automatically access school learning records.
  - A teacher belongs to **exactly one school** (`AUTH-03`) and accesses only assigned classes/subject offerings.
  - A student belongs to one school after enrollment approval (`AUTH-02`) and sees only their own records (`PROG-01`).
  - A parent/guardian may link to children across **multiple schools** (`AUTH-04`), seeing only approved children's grades, attendance, and teacher feedback (`PROG-02`).
  - Login accounts are separate from school memberships/roles.
- **Secrets & config:** Never hardcode secrets, database passwords, or fallback secret strings in source code. Load from environment variables / `.env` and fail fast if missing. Never commit `.env`.
- **Database safety:** Use SQLAlchemy ORM or parameterized queries only — never concatenate user input into SQL. Never expose raw SQL errors or stack traces in API responses.
- **Passwords & tokens:** Hash passwords with Argon2 or bcrypt (never plaintext). Use expiring, single-use tokens/codes for invitations and verification, storing only hashes.
- **File uploads (Slice 6+):** Enforce allow-listed file types (extension + content/magic bytes) and size limits; store with random UUID filenames outside public web paths; authorize every download.
- **Audit trail:** Record administrator decisions, role changes, enrollment changes, guardian link approvals/revocations, grade changes, and attendance changes.
- **HTTP & CORS:** Never use wildcard `*` in `CORS_ORIGINS`. Preserve security headers (`X-Content-Type-Options`, `X-Frame-Options`, CSP, `Cache-Control: no-store`).
- **Local testing:** Always bind local dev/test servers to `127.0.0.1` or `localhost`, never `0.0.0.0`.

## 5. Standard Backend Commands

Run from `backend/` using the local virtual environment (`backend/.venv`):

```powershell
# Run automated tests
.\.venv\Scripts\python.exe -m pytest -v

# Start local dev server
.\.venv\Scripts\uvicorn.exe app.main:create_app --factory --host 127.0.0.1 --port 8000 --reload

# Check Alembic migration status
.\.venv\Scripts\alembic.exe current
.\.venv\Scripts\alembic.exe upgrade head
```

## 6. Git Conventions

- Default branch is `master`.
- Never commit `.env`, `.venv/`, or local database dumps.
- Use clear, scoped commit messages referencing the slice or change (e.g., `feat(auth): add school memberships and login (Slice 2)`).
