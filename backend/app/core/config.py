"""Application configuration."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App settings loaded from environment variables."""

    APP_NAME: str = "TopoOpt Web"
    DEBUG: bool = False

    # File paths
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", str(Path(__file__).parent.parent.parent / "uploads"))
    RESULTS_DIR: str = os.getenv("RESULTS_DIR", str(Path(__file__).parent.parent.parent / "results"))

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Solver
    MAX_ITERATIONS: int = 200
    DEFAULT_VOLUME_FRACTION: float = 0.4
    DEFAULT_PENALTY: float = 3.0
    DEFAULT_FILTER_RADIUS: float = 1.5

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
