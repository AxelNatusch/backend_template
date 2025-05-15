import os

from pydantic import BaseModel


class Settings(BaseModel):
    """
    Application settings loaded from environment variables.
    """

    # Base settings
    APP_NAME: str = "DocuRead"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "Backend service for DocuRead"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # API Settings
    API_V1_STR: str = "/v1"

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:8000"
    ).split(",")

    # Logging
    LOG_LEVEL: str = "DEBUG" if DEBUG else "INFO"
    SEQ_URL: str = os.getenv("SEQ_URL", "http://localhost:5341")
    SEQ_API_KEY: str = os.getenv("SEQ_API_KEY", None)

    API_KEY_PREFIX: str = "dr"
    
    # Admin user settings
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@example.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin")


    # JWT settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "secret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", 7))

settings = Settings()
