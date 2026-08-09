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
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "") # Empty defaults to hybrid store
    
    CORS_ORIGINS: list = ["*"]

settings = Settings()
