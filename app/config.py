from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Prisoner DB RAG Chatbot"
    app_env: str = "dev"
    debug: bool = False

    db_dsn: str = Field(default="", description="Oracle DSN")
    db_user: str = Field(default="", description="Oracle read-only username")
    db_password: str = Field(default="", description="Oracle read-only password")
    db_timeout_sec: int = 8
    default_row_limit: int = 20

    llm_provider: str = "mock"
    llm_model: str = "gpt-4.1-mini"
    openai_api_key: str = ""

    allowed_objects: List[str] = [
        "PRI_PRISONER_VIEW",
        "PRI_RELEASE_VIEW",
        "PRI_PRISONER_LABOR_VIEW",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
