import re
from typing import Iterable

BLOCKED_PATTERNS = [
    r";",
    r"\bDROP\b",
    r"\bUPDATE\b",
    r"\bDELETE\b",
    r"\bMERGE\b",
    r"\bINSERT\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bCREATE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
]


def _has_where_clause(sql: str) -> bool:
    return bool(re.search(r"\bWHERE\b", sql, flags=re.IGNORECASE))


def _is_select_only(sql: str) -> bool:
    return bool(re.match(r"^\s*SELECT\b", sql, flags=re.IGNORECASE))


def _extract_from_objects(sql: str) -> set[str]:
    tokens = re.findall(r"\b(?:FROM|JOIN)\s+([A-Z0-9_\.]+)", sql.upper())
    cleaned = {token.split(".")[-1] for token in tokens}
    return cleaned


def validate_sql(sql: str, allowed_objects: Iterable[str]) -> str:
    normalized = sql.strip()
    if not normalized:
        raise ValueError("SQL хоосон байна.")

    if not _is_select_only(normalized):
        raise ValueError("Зөвхөн SELECT query зөвшөөрнө.")

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            raise ValueError("Аюултай SQL илэрлээ.")

    used_objects = _extract_from_objects(normalized)
    allow = {obj.upper() for obj in allowed_objects}
    if not used_objects:
        raise ValueError("FROM/JOIN объект тодорхойгүй SQL байна.")

    illegal = [obj for obj in used_objects if obj not in allow]
    if illegal:
        raise ValueError(f"Allowlist-оос гадуур объект ашигласан: {', '.join(illegal)}")

    return normalized


def ensure_row_limit(sql: str, default_limit: int) -> str:
    upper = sql.upper()
    if "FETCH FIRST" in upper or "ROWNUM" in upper:
        return sql

    if _has_where_clause(sql):
        return f"{sql} FETCH FIRST {default_limit} ROWS ONLY"

    return f"SELECT * FROM ({sql}) WHERE ROWNUM <= {default_limit}"
