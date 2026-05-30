from pathlib import Path

from poke_images.core.config import settings


def get_image_path(name: str) -> Path | None:
    """Resolve the artwork file for ``name`` inside the images folder.

    Returns the path if the file exists, otherwise ``None``. The lookup is a
    single stat() against ``{images_dir}/{name}{image_ext}`` — this is the
    File Server / S3 stand-in described in the architecture diagram.
    """
    path = settings.images_dir / f"{name}{settings.image_ext}"
    if path.is_file():
        return path
    return None
