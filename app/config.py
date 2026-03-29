import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    GOOGLE_SHEET_ID: str = "1ee33pBrtBoF-vXHTx_VIiAi5rFq0XRabHVqjFScL1LY"
    GOOGLE_SHEET_ID2: Optional[str] = None
    GOOGLE_CREDENTIALS_PATH: str = "credentials/service_account.json"
    DEBUG: bool = True
    APP_TITLE: str = "Auditor Tracking Dashboard - AIG"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

settings = Settings()
