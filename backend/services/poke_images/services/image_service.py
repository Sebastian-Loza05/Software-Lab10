from pathlib import Path

from commons.latency import latency_block
from poke_images.repositories import image_repository


def find_image(name: str) -> Path | None:
    # Names are stored lowercase by ingest_images.py; normalize the lookup so it
    # is case-insensitive like the Stats service.
    with latency_block("image_lookup"):
        return image_repository.get_image_path(name.strip().lower())
