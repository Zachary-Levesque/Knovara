"""Runtime configuration for the Knovara backend."""
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent
ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    """Typed backend settings loaded from environment variables."""

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_chat_model: str = Field(default="gpt-4o-mini", alias="OPENAI_CHAT_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        alias="OPENAI_EMBEDDING_MODEL",
    )
    chroma_persist_dir: str = Field(default="./.chroma", alias="CHROMA_PERSIST_DIR")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("cors_origins")
    @classmethod
    def require_cors_origins(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("CORS_ORIGINS must contain at least one origin.")
        return value

    @property
    def parsed_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

OPENAI_API_KEY = settings.openai_api_key
OPENAI_CHAT_MODEL = settings.openai_chat_model
OPENAI_EMBEDDING_MODEL = settings.openai_embedding_model
CHROMA_PERSIST_DIR = settings.chroma_persist_dir
CORS_ORIGINS = settings.parsed_cors_origins
