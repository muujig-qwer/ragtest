from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=2000,
        description="Natural-language user question in Mongolian.",
        examples=[
            "1607070011 дугаартай хоригдлын ерөнхий мэдээлэл",
            "Хамгийн сүүлд хэн хоригдол суллагдсан бэ?",
        ],
    )
    role: Literal["user", "developer", "admin", "officer"] = Field(
        default="user",
        description="Optional. Omit for normal users. Use developer/admin only when SQL preview is needed.",
    )


class ChatMeta(BaseModel):
    row_count: int
    latency_ms: int
    sql: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    meta: ChatMeta
