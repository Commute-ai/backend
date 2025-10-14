import secrets

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "Commute.ai"
    PROJECT_DESCRIPTION: str = "AI-powered public transport routing"
    VERSION: str = "0.4.0"
    API_V1_STR: str = "/api/v1"

    # JWT Settings
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # HSL API Settings
    HSL_ROUTING_API_URL: str = "https://api.digitransit.fi/routing/v2/hsl/gtfs/v1"
    HSL_SUBSCRIPTION_KEY: str = ""

    class ConfigDict:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
