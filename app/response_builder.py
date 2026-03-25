from datetime import date, datetime
from typing import Any, Dict, List

SENSITIVE_KEYS = {
    "REGISTER_NO",
    "PHONE",
    "ADDRESS",
    "SECRET",
    "PASSWORD",
    "STATE_REG_NUMBER",
}
PRIORITY_KEYS = [
    "PRISONER_ID",
    "PRISONER_NUMBER",
    "LAST_NAME",
    "FIRST_NAME",
    "NICKNAME",
    "WFM_STATUS_NAME",
    "LABOR_TYPE",
    "START_DATE",
    "END_DATE",
    "RELEASE_DATE",
    "RELEASE_TYPE",
    "STATUS",
    "DATE_OF_BIRTH",
    "STATE_REG_NUMBER",
]
NOISY_KEYS = {
    "PICTURE_PATH",
    "PERSON_ID",
    "WFM_STATUS_ID",
    "CREATED_DATE",
    "CREATED_BY",
    "DEPARTMENT_ID",
}


def mask_row(row: Dict[str, Any]) -> Dict[str, Any]:
    masked: Dict[str, Any] = {}
    for key, value in row.items():
        if key.upper() in SENSITIVE_KEYS and value is not None:
            masked[key] = "***"
        else:
            masked[key] = value
    return masked


def _display_value(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _compact_row(row: Dict[str, Any]) -> Dict[str, Any]:
    compact: Dict[str, Any] = {}

    for key in PRIORITY_KEYS:
        if key in row and row[key] not in (None, ""):
            compact[key] = row[key]

    if compact:
        return compact

    for key, value in row.items():
        if key.upper() in NOISY_KEYS or value in (None, ""):
            continue
        compact[key] = value
        if len(compact) >= 8:
            break

    return compact or row


def _person_label(row: Dict[str, Any]) -> str:
    last_name = row.get("LAST_NAME")
    first_name = row.get("FIRST_NAME")
    nickname = row.get("NICKNAME")
    prisoner_number = row.get("PRISONER_NUMBER")

    full_name = " ".join(part for part in [last_name, first_name] if part)
    if not full_name:
        full_name = "Нэр тодорхойгүй"

    details = []
    if prisoner_number:
        details.append(f"дугаар {prisoner_number}")
    if nickname and str(nickname).lower() not in {"none", "null", "үгүй"}:
        details.append(f"дуудлага нэр {nickname}")

    if details:
        return f"{full_name} ({', '.join(details)})"
    return full_name


def _format_prisoner_row(row: Dict[str, Any]) -> str:
    person = _person_label(row)
    status = row.get("WFM_STATUS_NAME")
    birth = row.get("DATE_OF_BIRTH")

    parts = [person]
    if status:
        parts.append(f"төлөв: {status}")
    if birth:
        parts.append(f"төрсөн огноо: {_display_value(birth)}")
    return ", ".join(parts) + "."


def _format_release_row(row: Dict[str, Any]) -> str:
    person = _person_label(row)
    release_date = row.get("RELEASE_DATE")
    release_type = row.get("RELEASE_TYPE")
    status = row.get("STATUS")

    parts = [person]
    if release_date:
        parts.append(f"суллагдсан огноо: {_display_value(release_date)}")
    if release_type:
        parts.append(f"төрөл: {release_type}")
    if status:
        parts.append(f"төлөв: {status}")
    return ", ".join(parts) + "."


def _format_labor_row(row: Dict[str, Any]) -> str:
    person = _person_label(row)
    labor_type = row.get("LABOR_TYPE")
    start_date = row.get("START_DATE")
    end_date = row.get("END_DATE")
    status = row.get("STATUS")

    parts = [person]
    if labor_type:
        parts.append(f"ажлын төрөл: {labor_type}")
    if start_date:
        parts.append(f"эхэлсэн: {_display_value(start_date)}")
    if end_date:
        parts.append(f"дууссан: {_display_value(end_date)}")
    if status:
        parts.append(f"төлөв: {status}")
    return ", ".join(parts) + "."


def _format_generic_row(row: Dict[str, Any]) -> str:
    compact_row = _compact_row(row)
    pairs = ", ".join(f"{k}={_display_value(v)}" for k, v in compact_row.items())
    return pairs + "."


def _format_row(row: Dict[str, Any]) -> str:
    if "RELEASE_DATE" in row:
        return _format_release_row(row)
    if "LABOR_TYPE" in row or "START_DATE" in row or "END_DATE" in row:
        return _format_labor_row(row)
    if "FIRST_NAME" in row or "LAST_NAME" in row or "WFM_STATUS_NAME" in row:
        return _format_prisoner_row(row)
    return _format_generic_row(row)


def build_mn_answer(rows: List[Dict[str, Any]]) -> str:
    if not rows:
        return "Тохирох өгөгдөл олдсонгүй."

    if len(rows) == 1:
        row = rows[0]
        if "RELEASE_DATE" in row:
            return f"Хамгийн ойрын тохирох суллалтын мэдээлэл: {_format_release_row(row)}"
        if "LABOR_TYPE" in row or "START_DATE" in row:
            return f"Хөдөлмөр эрхлэлтийн мэдээлэл: {_format_labor_row(row)}"
        if "FIRST_NAME" in row or "LAST_NAME" in row:
            return f"Хоригдлын мэдээлэл: {_format_prisoner_row(row)}"
        return f"Тохирох мэдээлэл олдлоо: {_format_generic_row(row)}"

    preview = rows[:5]

    if "RELEASE_DATE" in rows[0]:
        lines = [f"Нийт {len(rows)} суллалтын мэдээлэл олдлоо. Хамгийн сүүлийн {len(preview)} мэдээлэл:"]
    elif "LABOR_TYPE" in rows[0] or "START_DATE" in rows[0]:
        lines = [f"Нийт {len(rows)} хөдөлмөр эрхлэлтийн мэдээлэл олдлоо. Эхний {len(preview)} мөр:"]
    elif "FIRST_NAME" in rows[0] or "LAST_NAME" in rows[0]:
        lines = [f"Нийт {len(rows)} тохирох хоригдлын мэдээлэл олдлоо. Эхний {len(preview)} мөр:"]
    else:
        lines = [f"Нийт {len(rows)} мөр өгөгдөл олдлоо. Эхний {len(preview)} мөр:"]

    for idx, row in enumerate(preview, start=1):
        lines.append(f"{idx}. {_format_row(row)}")

    if len(rows) > len(preview):
        lines.append("Үлдсэн мөрүүдийг товчилж харууллаа.")

    return "\n".join(lines)
