import hashlib
import hmac
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.errors import AppError

# Argon2id with memory-hard defaults and unique per-password salts.
# TODO(security): Consider adding MFA, OAuth/SSO providers, and leaked-password
# screening (e.g., HIBP k-anonymity) before production launch.
_password_hasher = PasswordHasher()

MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128


def validate_password_strength(password: str) -> None:
    """Enforce password length policy without arbitrary character-class bans."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise AppError(
            status_code=422,
            code="WEAK_PASSWORD",
            message=f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.",
        )
    if len(password) > MAX_PASSWORD_LENGTH:
        raise AppError(
            status_code=422,
            code="PASSWORD_TOO_LONG",
            message=f"Password must not exceed {MAX_PASSWORD_LENGTH} characters.",
        )


def hash_password(password: str) -> str:
    validate_password_strength(password)
    return _password_hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def generate_token(num_bytes: int = 32) -> str:
    """Generate a cryptographically secure random URL-safe token."""
    return secrets.token_urlsafe(num_bytes)


def hash_token(raw_token: str) -> str:
    """Compute a SHA-256 hex digest for storing high-entropy tokens safely."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def constant_time_equals(expected_hash: str, candidate_raw_token: str) -> bool:
    candidate_hash = hash_token(candidate_raw_token)
    return hmac.compare_digest(expected_hash, candidate_hash)
