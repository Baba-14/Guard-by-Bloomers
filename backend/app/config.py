"""Runtime configuration for the local Guard API."""

from functools import lru_cache
from pathlib import Path
import os

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


class Settings:
    database_url = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://localhost:5432/guard"
    )
    jwt_secret = os.getenv("JWT_SECRET", "")
    jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    cors_origins = tuple(
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    )
    jev_api_key = os.getenv("JEV_API_KEY", "")
    jev_base_url = os.getenv("JEV_BASE_URL", "https://api.typesafe.ai").rstrip("/")
    jev_model = os.getenv("JEV_MODEL", "jev-latest")
    jev_timeout_seconds = float(os.getenv("JEV_TIMEOUT_SECONDS", "5"))
    analysis_persistence_enabled = os.getenv(
        "ANALYSIS_PERSISTENCE_ENABLED", "false"
    ).lower() in {"1", "true", "yes", "on"}
    analysis_database_lookup_enabled = os.getenv(
        "ANALYSIS_DATABASE_LOOKUP_ENABLED",
        os.getenv("ANALYSIS_PERSISTENCE_ENABLED", "false"),
    ).lower() in {"1", "true", "yes", "on"}
    store_analysis_content = os.getenv("STORE_ANALYSIS_CONTENT", "false").lower() in {
        "1", "true", "yes", "on"
    }

    def require_jwt_secret(self) -> str:
        if len(self.jwt_secret) < 32:
            raise RuntimeError(
                "JWT_SECRET must be configured with at least 32 characters in backend/.env"
            )
        return self.jwt_secret


@lru_cache
def get_settings() -> Settings:
    return Settings()
