"""
LocalVest Configuration Settings
Centralized configuration management for 0-Cost Environment & Production Deployment.
"""

import os

class Settings:
    PROJECT_NAME: str = "LocalVest API"
    VERSION: str = "2.0.0"
    API_PREFIX: str = "/api"
    
    JWT_SECRET: str = os.getenv("JWT_SECRET", "localvest_super_secret_python_key_2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    
    MOMO_SECRET_KEY: str = os.getenv("MOMO_SECRET_KEY", "localvest_momo_secret_123")
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "") # Empty defaults to hybrid store
    
    # SMTP Gmail Email Settings
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER: str = os.getenv("SMTP_USER", "")         # Ví dụ: localvest.app@gmail.com
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "") # Mật khẩu ứng dụng Gmail (16 ký tự)
    SMTP_FROM_NAME: str = "LocalVest System"

    # OTP & Environment Settings
    OTP_PROVIDER: str = os.getenv("OTP_PROVIDER", "mock")  # 'mock' hoặc 'real'
    ENV: str = os.getenv("ENV", "dev")                     # 'dev', 'test', 'prod'

    CORS_ORIGINS: list = ["*"]

settings = Settings()
