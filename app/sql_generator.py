import re
from typing import Iterable


def _escape_sql_string(value: str) -> str:
    return value.replace("'", "''").strip()


def _extract_identifier(question: str) -> str | None:
    match = re.search(r"\b\d{4,}\b", question)
    return match.group(0) if match else None


def _extract_name_token(question: str) -> str | None:
    quoted = re.search(r"['\"]([^'\"]{2,80})['\"]", question)
    if quoted:
        return quoted.group(1).strip()

    prisoner_match = re.search(r"хоригдол\s+([^\s,?.!]{2,40})", question, re.IGNORECASE)
    if prisoner_match:
        token = prisoner_match.group(1).strip()
        if token.lower() != "x":
            return token
    return None


def _prisoner_where_clause(question: str) -> str:
    identifier = _extract_identifier(question)
    lowered = question.lower()

    if identifier:
        if "дугаар" in lowered or "number" in lowered:
            return f" WHERE PRISONER_NUMBER = '{identifier}'"
        if re.search(r"\bid\b", lowered):
            return f" WHERE PRISONER_ID = {identifier}"
        return (
            " WHERE PRISONER_ID = "
            f"{identifier} OR PRISONER_NUMBER = '{identifier}'"
        )

    name_token = _extract_name_token(question)
    if name_token:
        safe_name = _escape_sql_string(name_token).upper()
        return (
            " WHERE UPPER(FIRST_NAME) LIKE '%"
            f"{safe_name}%' OR UPPER(LAST_NAME) LIKE '%{safe_name}%'"
            f" OR UPPER(NICKNAME) LIKE '%{safe_name}%'"
        )

    return ""


def generate_sql(question: str, allowed_objects: Iterable[str]) -> str:
    q = question.lower()
    allow = {obj.upper() for obj in allowed_objects}
    where_clause = _prisoner_where_clause(question)
    asks_latest = any(token in q for token in ["хамгийн сүүлд", "сүүлийн", "latest", "most recent"])
    asks_who = "хэн" in q or "who" in q

    if "release" in q or "шилжилт" in q or "суллагдсан" in q:
        target = "PRI_RELEASE_VIEW"
        if target in allow:
            if "PRI_PRISONER_VIEW" in allow and (asks_latest or asks_who):
                latest_suffix = " FETCH FIRST 1 ROWS ONLY" if asks_latest else ""
                return (
                    "SELECT r.PRISONER_ID, r.PRISONER_NUMBER, p.LAST_NAME, p.FIRST_NAME, "
                    "p.NICKNAME, r.RELEASE_DATE, r.RELEASE_TYPE, r.STATUS "
                    "FROM PRI_RELEASE_VIEW r "
                    "JOIN PRI_PRISONER_VIEW p ON p.PRISONER_ID = r.PRISONER_ID"
                    f"{where_clause} ORDER BY r.RELEASE_DATE DESC{latest_suffix}"
                )

            latest_suffix = " FETCH FIRST 1 ROWS ONLY" if asks_latest else ""
            return (
                "SELECT PRISONER_ID, PRISONER_NUMBER, RELEASE_DATE, RELEASE_TYPE, STATUS "
                f"FROM PRI_RELEASE_VIEW{where_clause} ORDER BY RELEASE_DATE DESC{latest_suffix}"
            )

    if "хөдөлмөр" in q or "labor" in q or "ажил" in q:
        target = "PRI_PRISONER_LABOR_VIEW"
        if target in allow:
            return (
                "SELECT PRISONER_ID, PRISONER_NUMBER, LABOR_TYPE, START_DATE, END_DATE, STATUS "
                f"FROM PRI_PRISONER_LABOR_VIEW{where_clause} ORDER BY START_DATE DESC"
            )

    target = "PRI_PRISONER_VIEW"
    if target in allow:
        base_sql = (
            "SELECT PRISONER_ID, PRISONER_NUMBER, FIRST_NAME, LAST_NAME, NICKNAME, "
            "DATE_OF_BIRTH, WFM_STATUS_NAME, STATE_REG_NUMBER "
            "FROM PRI_PRISONER_VIEW"
        )
        if where_clause:
            return f"{base_sql}{where_clause} ORDER BY PRISONER_ID DESC"
        return f"{base_sql} ORDER BY PRISONER_ID DESC"

    first = next(iter(allow), None)
    if not first:
        raise ValueError("Allowlist хоосон байна.")
    return f"SELECT * FROM {first}"
