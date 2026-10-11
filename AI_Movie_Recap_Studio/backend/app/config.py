import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "AI Movie Recap Studio"
    ENV: str = "production"
    DEBUG: bool = False
    
    # Security & Encryption
    SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE_THIS_TO_A_64_CHAR_HEX_KEY_IN_PRODUCTION")
    ENCRYPTION_SECRET_KEY: str = os.getenv("ENCRYPTION_SECRET_KEY", "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 Days
    ALGORITHM: str = "HS256"
    
    # Registration & Beta Mode
    INVITE_ONLY: bool = True
    REGISTRATION_INVITE_CODE: str = os.getenv("REGISTRATION_INVITE_CODE", "BETAMONKEY2026")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./storage/recap_studio.db")
    
    # File Storage & Limits
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "./storage")
    MAX_UPLOAD_BYTES: int = 500 * 1024 * 1024       # 500 MB
    MAX_STORAGE_PER_USER_BYTES: int = 2 * 1024 * 1024 * 1024  # 2 GB
    MAX_SOURCE_DURATION_SEC: int = 7200             # 2 Hours
    MAX_OUTPUT_DURATION_SEC: int = 900              # 15 Minutes
    
    # Worker Concurrency & Hardware Limits
    MAX_CONCURRENT_RENDERS_GLOBAL: int = 2
    MAX_CONCURRENT_RENDERS_PER_USER: int = 1
    JOB_TIMEOUT_SECONDS: int = 1800                 # 30 Minutes
    
    # AI Default / Admin Keys (Optional BYOK fallback)
    ASSEMBLYAI_ADMIN_KEY: Optional[str] = os.getenv("ASSEMBLYAI_ADMIN_KEY", None)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY", None)
    
    # System Maintenance
    MAINTENANCE_MODE: bool = False

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
