from poke_images.core.config import settings


def check_storage() -> bool:
    try:
        return settings.images_dir.is_dir()
    except Exception:
        return False
