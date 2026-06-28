"""
Environment variables and settings.

This file loads Knovara backend configuration from backend/.env and the process
environment, exposes typed settings for Gemini, Chroma, and CORS, and fails
loudly during startup when required secrets are missing.
"""
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent
ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    """Typed backend settings loaded from environment variables."""

    gemini_api_key: str = Field(alias="GEMINI_API_KEY")
    gemini_chat_model: str = Field(
        default="gemini-1.5-flash",
        alias="GEMINI_CHAT_MODEL",
    )
    gemini_embedding_model: str = Field(
        default="models/text-embedding-004",
        alias="GEMINI_EMBEDDING_MODEL",
    )
    chroma_persist_dir: str = Field(default="./.chroma", alias="CHROMA_PERSIST_DIR")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("gemini_api_key")
    @classmethod
    def require_gemini_api_key(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError(
                "GEMINI_API_KEY is required. Set it in backend/.env or the "
                "process environment before starting the backend."
            )
        return value

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

GEMINI_API_KEY = settings.gemini_api_key
GEMINI_CHAT_MODEL = settings.gemini_chat_model
GEMINI_EMBEDDING_MODEL = settings.gemini_embedding_model
CHROMA_PERSIST_DIR = settings.chroma_persist_dir
CORS_ORIGINS = settings.parsed_cors_origins