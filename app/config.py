from pathlib import Path
import os
from pydantic import BaseModel


class Settings(BaseModel):
    """Centralized app settings for local-first deployment."""

    app_name: str = "RunTech MK1"
    sqlite_path: Path = Path("data/runtech.db")
    strava_base_url: str = "https://www.strava.com/api/v3"
    oauth_token_url: str = "https://www.strava.com/oauth/token"
    strava_page_size: int = 100
    strava_rate_limit_buffer_seconds: int = 2
    acwr_soft_max: float = 1.3
    acwr_hard_max: float = 1.5
    llm_mode: str = os.getenv("LLM_MODE", "local_stub")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "phi3:mini")


settings = Settings()
