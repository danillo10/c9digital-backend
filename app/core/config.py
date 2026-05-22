from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()


def _resolve_database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip() or "sqlite:///./c9digital.db"
    # Railway pode estar configurado com /c9digital antes do banco existir
    if "/c9digital" in url:
        url = url.replace("/c9digital", "/railway")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Settings(BaseSettings):
    DATABASE_URL: str = _resolve_database_url()
    SECRET_KEY: str = os.getenv("SECRET_KEY", "c9digital-dev-secret-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"


settings = Settings()
