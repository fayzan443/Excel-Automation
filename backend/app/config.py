"""
Configuration settings for the Excel-Cleaner backend.
Loads environment variables and application settings.
"""

from pydantic_settings import BaseSettings  # updated for Pydantic v2
from pathlib import Path

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Excel-Cleaner"
    DEBUG: bool = True
    
    # File settings
    UPLOAD_FOLDER: str = "uploads"
    ALLOWED_EXTENSIONS: set = {"xlsx", "xls", "csv"}
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB max file size

    # Environment file settings
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

# Initialize settings
settings = Settings()

# Ensure uploads directory exists
Path(settings.UPLOAD_FOLDER).mkdir(exist_ok=True)
