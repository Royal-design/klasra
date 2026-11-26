"""Shared input normalization helpers for Pydantic request schemas."""


def normalize_whitespace(value: str | None) -> str | None:
    """Trim leading/trailing whitespace and collapse internal runs to single spaces."""
    if value is None:
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


def normalize_required_text(value: str) -> str:
    """Collapse whitespace on required text fields (preserves intentional name casing)."""
    return " ".join(value.split())


def normalize_title_label(value: str) -> str:
    """Collapse whitespace and title-case display labels (e.g. 'legal  guardian' -> 'Legal Guardian')."""
    return " ".join(value.split()).title()


def normalize_upper_code(value: str) -> str:
    """Trim, collapse whitespace, and uppercase short codes (e.g. 'math101' -> 'MATH101')."""
    return " ".join(value.split()).upper()


def normalize_optional_upper_code(value: str | None) -> str | None:
    """Normalize optional short codes (e.g. letter grades, student references) to uppercase or None."""
    if value is None:
        return None
    cleaned = " ".join(value.split()).upper()
    return cleaned or None


def normalize_enum_str(value: object) -> object:
    """Lowercase and strip string inputs before Pydantic Literal validation."""
    if isinstance(value, str):
        return value.strip().lower()
    return value
