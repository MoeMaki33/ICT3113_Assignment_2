import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _float_env(name: str, default: float) -> float:
    """Read a positive float from the environment; fall back to default if unusable."""
    try:
        value = float(os.getenv(name, ""))
    except ValueError:
        return default
    return value if value > 0 else default


@dataclass(frozen=True)
class Settings:
    ollama_url: str = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
    # Exact Ollama tag from docs/models.md. Change it in .env / the environment to
    # switch candidate model; no source edit is needed (see docs/models.md).
    ollama_model: str = os.getenv("OLLAMA_MODEL", "")
    # Seconds to wait for one blocking classification request.
    ollama_timeout: float = _float_env("OLLAMA_TIMEOUT_SECONDS", 120.0)
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/tickets.db")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    classification_mode: str = os.getenv("CLASSIFICATION_MODE", "single").strip().lower()
    cascade_small_model: str = os.getenv("CASCADE_SMALL_MODEL", "llama3.2:3b").strip()
    cascade_large_model: str = os.getenv("CASCADE_LARGE_MODEL", "llama3.1:8b").strip()
    cascade_setting: str = os.getenv("CASCADE_SETTING", "A").strip().upper()


settings = Settings()
