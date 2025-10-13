import secrets

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Commute.ai"
    PROJECT_DESCRIPTION: str = "AI-powered public transport routing"
    VERSION: str = "0.3.0"
    API_V1_STR: str = "/api/v1"

    # JWT Settings
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class ConfigDict:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
