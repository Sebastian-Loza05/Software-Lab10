from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
# services/poke_images -> services -> backend (project root that holds data/)
PROJECT_ROOT = BASE_DIR.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env", BASE_DIR / ".env.local"),
        extra="ignore",
    )

    # Flat folder of {name}.jpg artwork that stands in for the File Server / S3.
    # Populated by scripts/ingest_images.py; override via IMAGES_DIR only if the
    # data lives elsewhere.
    images_dir: Path = PROJECT_ROOT / "data" / "images"
    image_ext: str = ".jpg"


settings = Settings()
