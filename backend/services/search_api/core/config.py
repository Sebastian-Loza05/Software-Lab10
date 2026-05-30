from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env", BASE_DIR / ".env.local"),
        extra="ignore",
    )

    # Downstream services orchestrated by the gateway.
    poke_api_url: str = "http://localhost:8001"
    poke_stats_url: str = "http://localhost:8002"
    poke_images_url: str = "http://localhost:8003"

    # Per-request timeout (seconds) applied to every downstream call.
    downstream_timeout: float = 5.0


settings = Settings()
