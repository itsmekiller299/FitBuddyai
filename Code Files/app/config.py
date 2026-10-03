from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


class Settings(BaseSettings):
    app_name: str = "FitBuddy"
    debug: bool = False
    database_url: str = "sqlite:///./data/fitbuddy.db"
    gemini_api_key: str | None = Field(default=None, validation_alias="GEMINI_API_KEY")
    gemini_workout_model: str = Field(default="gemini-3.1-pro-preview", validation_alias="GEMINI_WORKOUT_MODEL")
    gemini_tip_model: str = Field(default="gemini-3.8-flash", validation_alias="GEMINI_TIP_MODEL")
    demo_mode: bool = Field(default=False, validation_alias="DEMO_MODE")
    admin_username: str = Field(default="admin", validation_alias="ADMIN_USERNAME")
    admin_password: str = Field(default="change-me", validation_alias="ADMIN_PASSWORD")

    model_config = SettingsConfigDict(env_file=str(ROOT_DIR / ".env"), extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
