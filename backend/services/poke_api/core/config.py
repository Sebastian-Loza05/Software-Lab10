from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env", BASE_DIR / ".env.local"),
        extra="ignore",
    )

    turso_url: str
    turso_token: str
    pokeapi_base_url: str = "https://pokeapi.co/api/v2"


settings = Settings()
