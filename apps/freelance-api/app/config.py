from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "freelance-template"
    env: Literal["dev", "test", "staging", "prod"] = "dev"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./data/freelance.db"
    api_token: str = "replace-with-your-token"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("api_token")
    @classmethod
    def validate_api_token(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("API_TOKEN 不能为空")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
