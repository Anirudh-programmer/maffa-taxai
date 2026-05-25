"""
Core application settings using Pydantic Settings.
Loads from environment variables / .env file.
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Maffa TaxAI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # API
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = "changethisinproduction"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # Clerk Auth
    CLERK_SECRET_KEY: str = ""
    CLERK_PUBLISHABLE_KEY: str = ""

    # Database
    DATABASE_URL: str = ""

    # AI
    GEMINI_API_KEY: str = "AIzaSyAqopMWrgEHAJ9SFU8DlqyrOOzyoj5pl2s"
    GEMINI_MODEL: str = "models/gemini-2.5-flash"
    GEMINI_FLASH_MODEL: str = "models/gemini-2.0-flash-lite"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    CHROMA_COLLECTION_NAME: str = "tax_knowledge"

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: List[str] = ["application/pdf", "image/jpeg", "image/png"]

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # SMTP / Email Configuration (Production Ready)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_SECURE: bool = True
    EMAILS_FROM_EMAIL: str = "noreply@taxai.app"
    EMAILS_FROM_NAME: str = "Maffa TaxAI Core"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    model_config = {"env_file": ".env", "case_sensitive": True, "extra": "ignore"}


settings = Settings()
