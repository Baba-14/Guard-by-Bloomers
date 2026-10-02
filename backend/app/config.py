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

    def require_jwt_secret(self) -> str:
        if len(self.jwt_secret) < 32:
            raise RuntimeError(
                "JWT_SECRET must be configured with at least 32 characters in backend/.env"
            )
        return self.jwt_secret


@lru_cache
def get_settings() -> Settings:
    return Settings()
