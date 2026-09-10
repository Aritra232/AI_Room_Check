from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


class Settings(BaseSettings):
    app_name: str = "Room AI Inspection Service"
    openai_api_key: str | None = None
    openai_model: str | None = None
    gemini_api_key: str
    gemini_model: str = "gemini-3.8-flash"
    database_url: str
    database_name: str
    storage_dir: Path = ROOT_DIR / "service" / "storage"
    annotated_dir: Path = ROOT_DIR / "Annotated"
    cors_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    settings.annotated_dir.mkdir(parents=True, exist_ok=True)
    return settings


settings = get_settings()
