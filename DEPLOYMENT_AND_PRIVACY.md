# DEPLOYMENT_AND_PRIVACY.md — Production Hardening, Backups & NDPA Privacy Checklist

This runbook covers **Slice 10** (production deployment, backups, monitoring, and privacy compliance) before launching School LMS to real schools and students.

---

## 1. Production Environment Checklist

Set these environment variables via your hosting provider's secrets manager (never commit `.env` or store secrets in source code):

| Variable | Production Value / Requirement |
| --- | --- |
| `APP_ENV` | `production` (disables `/docs`, `/redoc`, `/openapi.json`; enforces `COOKIE_SECURE=true` and JSON logging) |
| `COOKIE_SECURE` | `true` (activates `__Host-lms_session` and `__Host-lms_csrf` over HTTPS) |
| `DATABASE_URL` | Least-privilege PostgreSQL user (never `postgres` superuser) with TLS/mTLS (`?sslmode=verify-full`) |
| `CORS_ORIGINS` | Exact production Next.js origin(s) over HTTPS (e.g., `https://app.yourdomain.com`); `*` is rejected |
| `EMAIL_PROVIDER` | `resend` with `RESEND_API_KEY` and SPF/DKIM/DMARC-verified `EMAIL_FROM` |
| `FRONTEND_BASE_URL` | Exact HTTPS frontend base URL used for invitation and password-reset links |
| `STORAGE_PROVIDER` | `s3` pointing to a **Private** bucket (Backblaze B2, Cloudflare R2, or AWS S3) with bucket-scoped keys |

### Pre-Launch Security Upgrades (`TODO(security)` items)
1. **Distributed rate limiter:** Replace the single-process in-memory limiter (`app/core/rate_limit.py`) with a Redis-backed limiter when running multiple Uvicorn workers or containers.
2. **Malware scanning & CDR:** Scan uploaded student/teacher files via an antivirus API (e.g., ClamAV sidecar or cloud AV API) before persisting to private storage.
3. **MFA / SSO:** Consider optional TOTP MFA for Platform Administrators and School Administrators.

---

## 2. Database Migrations & Automated Backups

- **Apply migrations during deployment (before starting new app containers):**
  ```bash
  alembic upgrade head
  ```
- **Daily encrypted PostgreSQL backups:**
  - Use managed automated snapshots (e.g., Neon, Supabase, RDS, Render Postgres) with **point-in-time recovery (PITR)** and encryption at rest.
  - Or run a scheduled `pg_dump --format=custom --no-owner` piped through encryption (KMS/age/GPG) into a separate private backup bucket with **30-day daily + 12-month monthly** retention.
- **Restore drill:** Test restoring a backup into a staging database at least once per quarter and verify `alembic current` + sample queries.
- **Object storage versioning:** Enable bucket versioning and lifecycle rules on your private B2/R2/S3 bucket so accidental deletions can be recovered.

---

## 3. Monitoring & Logging

- **Liveness / Readiness probe:** Point your load balancer or container healthcheck to `GET /api/v1/health` (`200 OK` when app + PostgreSQL are healthy; `503 Service Unavailable` when DB is unreachable).
- **Structured logs:** In `APP_ENV=production`, `app/core/logging.py` emits JSON logs with `request_id` (`X-Request-ID` header), `method`, `path`, `status_code`, and `duration_ms`.
- **PII protection in logs:** Never log cookies, `X-CSRF-Token`, passwords, invitation/reset tokens, or student PII.
- **Recommended alerts:**
  - `GET /api/v1/health` returning non-200 for > 1 minute
  - `5xx` error rate spike
  - Sustained `429 RATE_LIMITED` spikes on `/api/v1/auth/login` (brute-force signal)
  - Resend email delivery failures in logs

---

## 4. Privacy & Child-Data Compliance Review (NDPA 2023)

Because School LMS serves **secondary-school students aged 12 and above**, complete this review with a qualified local privacy contact before onboarding real schools (if launching in Nigeria, align with the **Nigeria Data Protection Act 2023 (NDPA)** and NDPC guidance):

1. **Data minimization:** Only collect fields required to operate school academic workflows (name, school contact/email, optional student reference, academic records).
2. **Role & tenant isolation:** Every school-owned record is scoped by `school_id`; parents see only approved children's grades, attendance, and teacher feedback (`PROG-02`); teachers belong to one school (`AUTH-03`).
3. **Consent & institutional authority:** Establish written Data Processing Agreements (DPAs) with each onboarding school confirming lawful basis and parent/guardian notice for minor students.
4. **Retention & deletion policy:** Define retention periods for graduated/withdrawn student records, uploaded assignment files, and `audit_events`, plus a documented process for school offboarding and verified deletion requests.
5. **Audit trail:** Preserve immutable `audit_events` for admin approvals, role changes, enrollments/transfers/withdrawals, guardian-link approvals/revocations, grade changes, and attendance edits.
6. **Incident response:** Document a 72-hour breach notification procedure covering affected schools, guardians, and the relevant supervisory authority (NDPC).
