import re
from typing import Iterable
from app.config import get_settings

try:
    from google import genai
except ImportError:
    genai = None

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

def _mock_generate_sql(question: str, allowed_objects: Iterable[str]) -> str:
    q = question.lower()
    allow = {obj.upper() for obj in allowed_objects}
    where_clause = _prisoner_where_clause(question)
    asks_latest = any(token in q for token in ["хамгийн сүүлд", "сүүлийн", "latest", "most recent"])
    asks_who = "хэн" in q or "who" in q

    if any(k in q for k in ["release", "шилжилт", "суллагдсан", "суллагдах", "сулласан", "sullagd", "sullagdsan", "гарсан", "garsan"]):
        target = "PRI_RELEASE_VIEW"
        if target in allow:
            if "PRI_PRISONER_VIEW" in allow and (asks_latest or asks_who):
                latest_suffix = " FETCH FIRST 1 ROWS ONLY" if asks_latest else ""
                return (
                    "SELECT r.PRISONER_ID, r.PRISONER_NUMBER, p.LAST_NAME, p.FIRST_NAME, "
                    "p.NICKNAME, r.RELEASE_DATE, p.WFM_STATUS_NAME AS STATUS "
                    "FROM PRI_RELEASE_VIEW r "
                    "JOIN PRI_PRISONER_VIEW p ON p.PRISONER_ID = r.PRISONER_ID"
                    f"{where_clause} ORDER BY r.RELEASE_DATE DESC{latest_suffix}"
                )
            latest_suffix = " FETCH FIRST 1 ROWS ONLY" if asks_latest else ""
            return (
                "SELECT PRISONER_ID, PRISONER_NUMBER, RELEASE_DATE "
                f"FROM PRI_RELEASE_VIEW{where_clause} ORDER BY RELEASE_DATE DESC{latest_suffix}"
            )

    if any(k in q for k in ["хөдөлмөр", "labor", "ажил", "ajil", "hodolmor", "hudulmur"]):
        target = "PRI_PRISONER_LABOR_VIEW"
        if target in allow:
            return (
                "SELECT PRISONER_ID, PRISONER_NUMBER, LABOR_TYPE, START_DATE, END_DATE "
                f"FROM PRI_PRISONER_LABOR_VIEW{where_clause} ORDER BY START_DATE DESC"
            )

    target = "PRI_PRISONER_VIEW"
    if target in allow:
        base_sql = "SELECT * FROM PRI_PRISONER_VIEW"
        if where_clause:
            return f"{base_sql}{where_clause} ORDER BY PRISONER_ID DESC"
        return f"{base_sql} ORDER BY PRISONER_ID DESC"

    first = next(iter(allow), None)
    if not first:
        raise ValueError("Allowlist хоосон байна.")
    return f"SELECT * FROM {first}"

def _gemini_generate_sql(question: str, allowed_objects: Iterable[str]) -> str:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise ValueError("Gemini API key is missing from .env (GEMINI_API_KEY).")
    
    client = genai.Client(api_key=settings.gemini_api_key)
    
    schema_info = """
Table: PRI_PRISONER_VIEW
Columns: PRISONER_ID, PRISONER_NUMBER, NICKNAME, PICTURE_PATH, PERSON_ID, WFM_STATUS_ID, CREATED_DATE, DEPARTMENT_ID, FIRST_NAME, LAST_NAME, STATE_REG_NUMBER, DATE_OF_BIRTH, GENDER_NAME, WFM_STATUS_NAME
Description: Хоригдлын үндсэн мэдээлэл

Table: PRI_RELEASE_VIEW
Columns: RELEASE_ID, PRISONER_KEY_ID, DECISION_ID, RELEASE_TYPE_ID, RELEASE_DATE, CREATED_DATE, CREATED_EMPLOYEE_KEY_ID, DESCRIPTION, IS_ROLLEDBACK, ROLLEDBACK_DATE, DEPARTMENT_ID, PRISONER_ID, PRISONER_NUMBER, STATE_REG_NUMBER, FIRST_NAME, LAST_NAME, DEPARTMENT_NAME, RELEASE_TYPE_NAME, DECISION_NUMBER, PERSON_ID, DETENTION_ID
Description: Хоригдлуудын суллагдсан түүх. Суллагдсан гэвэл эндээс хайна.

Table: PRI_PRISONER_LABOR_VIEW
Columns: PRISONER_LABOR_ID, LABOR_ID, PRISONER_KEY_ID, PRISONER_NAME, REGISTER_NO, LABOR_TYPE_ID, LABOR_TYPE_NAME, BEGIN_DATE, END_DATE, WFM_STATUS_ID, STATUS_NAME, IS_SALARY, LABOR_RESULT_TYPE_ID, LABOR_RESULT_TYPE_NAME, DESCRIPTION, CREATED_DATE, DEPARTMENT_NAME, DEPARTMENT_ID, CREATED_EMPLOYEE_NAME
Description: Хөдөлмөр эрхлэлтийн түүх.
"""
    
    prompt = f"""
Та бол Oracle мэдээллийн сангийн өндөр түвшний SQL бичигч туслах.
Доорх өгөгдлийн баазын бүтэц болон дүрмийг дагаж Хэрэглэгчийн асуултад тохирох зөвхөн ганц Oracle SQL query буцаана уу. Юу ч битгий тайлбарла, зөвхөн SQL бич.

Зөвшөөрөгдсөн View-нүүд: {', '.join(allowed_objects)}

Bаазын бүтэц:
{schema_info}

Дүрэм:
1. ЗӨВХӨН SELECT үйлдэл ашиглана. UPDATE, DELETE, INSERT хориотой.
2. WHERE нөхцөлд текстийг хайх үед үсгэн жижиг томоос хамаарахгүй байх үүднээс UPPER() болон LIKE '%...%' ашиглах нь дээр.
3. Үр дүнг эрэмбэлэхдээ утгаараа DESC эсвэл ASC. 
4. Зөвхөн дээр дурдсан зөвшөөрөгдсөн View-нүүдтэй л JOIN хийж эсвэл шууд хандаж болно.
5. Хариу нь ямар нэгэн markdown (```sql гэх мэт) болон тайлбаргүй ЦЭВЭР SQL текст байх ёстой. Хэрвээ "хамгийн сүүлд" эсвэл цөөн илэрц гэвэл FETCH FIRST N ROWS ONLY ашиглах.

Хэрэглэгчийн асуулт: {question}
"""
    
    response = client.models.generate_content(
        model=settings.llm_model,
        contents=prompt
    )
    sql = response.text.replace('```sql', '').replace('```', '').strip()
    return sql

def generate_sql(question: str, allowed_objects: Iterable[str]) -> str:
    settings = get_settings()
    if settings.llm_provider == "gemini":
        if genai is None:
            raise RuntimeError("google-genai package is not installed. Please pip install it first.")
        return _gemini_generate_sql(question, allowed_objects)
    
    return _mock_generate_sql(question, allowed_objects)
