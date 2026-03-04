from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Plumbing Product Detection Engine"
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/plumbing"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    tesseract_cmd: str | None = None
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
