from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "freelance-template"
    env: str = "dev"
    database_url: str = "sqlite:///./data/freelance.db"
    api_token: str = "replace-with-your-token"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
