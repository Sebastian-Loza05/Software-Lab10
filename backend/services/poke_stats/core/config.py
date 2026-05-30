from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env", BASE_DIR / ".env.local"),
        extra="ignore",
    )

    turso_database_url: str
    turso_auth_token: str

    @property
    def turso_pipeline_url(self) -> str:
        return self.turso_database_url.rstrip("/") + "/v2/pipeline"


settings = Settings()
