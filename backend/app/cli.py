"""CLI utilities for administrative bootstrap tasks.

Usage (from backend/):
    python -m app.cli create-platform-admin --email admin@example.com --full-name "Platform Admin"
"""

import argparse
import getpass
import sys

from app.core.errors import AppError
from app.core.security import hash_password
from app.db.session import get_session_factory
from app.models.user import User
from app.repositories import user_repo
from app.services.audit import record_audit_event


def create_platform_admin(email: str, full_name: str, password: str) -> User:
    normalized_email = email.strip().lower()
    session_factory = get_session_factory()
    with session_factory() as db:
        if user_repo.get_user_by_email(db, email=normalized_email) is not None:
            raise AppError(
                status_code=409,
                code="USER_EMAIL_EXISTS",
                message=f"User with email '{normalized_email}' already exists.",
            )

        user = user_repo.create_user(
            db,
            email=normalized_email,
            full_name=full_name,
            password_hash=hash_password(password),
            is_platform_admin=True,
            is_active=True,
        )
        db.flush()

        record_audit_event(
            db,
            action="platform_admin.bootstrapped",
            target_type="user",
            target_id=user.id,
            actor_user_id=user.id,
            metadata={"email": normalized_email},
        )
        db.commit()
        db.refresh(user)
        return user


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli", description="School LMS admin CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    admin_parser = subparsers.add_parser(
        "create-platform-admin", help="Create a platform administrator account"
    )
    admin_parser.add_argument("--email", required=True, help="Admin email address")
    admin_parser.add_argument("--full-name", required=True, help="Admin full name")
    admin_parser.add_argument(
        "--password",
        required=False,
        help="Admin password (omit to enter securely via prompt)",
    )

    args = parser.parse_args(argv)
    if args.command == "create-platform-admin":
        password = args.password or getpass.getpass("Password (min 12 chars): ")
        try:
            user = create_platform_admin(
                email=args.email,
                full_name=args.full_name,
                password=password,
            )
        except AppError as exc:
            print(f"Error [{exc.code}]: {exc.message}", file=sys.stderr)
            return 1

        print(f"Created platform administrator: {user.email} (id={user.id})")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
