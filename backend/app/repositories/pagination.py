from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session


def count_and_paginate_scalars(
    db: Session,
    stmt: Select[Any],
    *,
    offset: int,
    limit: int,
) -> tuple[list[Any], int]:
    total = int(
        db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    )
    items = list(db.scalars(stmt.offset(offset).limit(limit)).all())
    return items, total


def count_and_paginate_rows(
    db: Session,
    stmt: Select[Any],
    *,
    offset: int,
    limit: int,
) -> tuple[list[Any], int]:
    total = int(
        db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    )
    rows = list(db.execute(stmt.offset(offset).limit(limit)).all())
    return rows, total


def escape_like(value: str) -> str:
    """Escape SQL LIKE wildcards so user search strings match literally."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
