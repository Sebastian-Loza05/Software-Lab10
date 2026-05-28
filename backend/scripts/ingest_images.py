#!/usr/bin/env python3
"""One-time ingest: Kaggle pokemon-image-dataset -> flat data/images/ (S3 stand-in).

Source dataset: https://www.kaggle.com/datasets/hlrhegemony/pokemon-image-dataset
Its actual structure (~898 folders, 2503 files):

    {source}/
      Charizard/
        0.jpg
        1.jpg
        ...
      Bulbasaur/
        0.jpg
        ...
      Flab├йb├й/        <- mojibake from cp437-mis-decoded zip
      NidoranтЩА/       <- Nidoran♀
      NidoranтЩВ/       <- Nidoran♂

This script flattens that into ``data/images/{pokeapi_name}.jpg`` so the POKE
Images service can serve ``GET /images/{name}`` with a single stat() call. We
pick ``0.jpg`` per folder as the canonical artwork (it is always present and is
the dataset's primary image). Names are normalized to the PokeAPI convention:
lowercase, hyphens for spaces, periods/apostrophes stripped, accented and
mojibake-corrupted folder names mapped explicitly.

The script never downloads anything: it processes whatever is at ``--source``.

    python scripts/ingest_images.py --source data/images/images
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = PROJECT_ROOT / "data" / "raw"
DEST_DIR = PROJECT_ROOT / "data" / "images"
BATCH_SIZE = 50

# Direct overrides for folder names we cannot derive via the general rule:
# the three names mangled by the zip's cp437 re-encoding, plus any pokemon
# whose folder differs from its canonical PokeAPI slug.
NAME_OVERRIDES: dict[str, str] = {
    "Flab├йb├й": "flabebe",        # Flabébé
    "NidoranтЩА": "nidoran-f",     # Nidoran♀
    "NidoranтЩВ": "nidoran-m",     # Nidoran♂
    "Mime Jr": "mime-jr",
    "Mr. Mime": "mr-mime",
    "Mr. Rime": "mr-rime",
    "Type Null": "type-null",
    "Farfetch'd": "farfetchd",
    "Sirfetch'd": "sirfetchd",
}

# General normalization: lowercase, drop ' and . and :, hyphenate whitespace,
# collapse repeats. Hyphens already in the source (Ho-oh, Porygon-Z, Kommo-o)
# are preserved.
_DROP = re.compile(r"[.'\":]+")
_SPACE = re.compile(r"\s+")
_DASHES = re.compile(r"-{2,}")


def normalize_name(folder: str) -> str:
    if folder in NAME_OVERRIDES:
        return NAME_OVERRIDES[folder]
    name = _DROP.sub("", folder.strip().lower())
    name = _SPACE.sub("-", name)
    name = _DASHES.sub("-", name).strip("-")
    return name


def pick_canonical(folder: Path) -> Path | None:
    """Return the canonical image inside a pokemon folder, or None if empty."""
    # 0.jpg is the dataset's primary; fall back to first sorted image otherwise.
    primary = folder / "0.jpg"
    if primary.is_file():
        return primary
    images = sorted(p for p in folder.iterdir()
                    if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    return images[0] if images else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--source", type=Path, default=DEFAULT_SOURCE,
        help=f"Root containing one folder per pokemon (default: {DEFAULT_SOURCE})",
    )
    args = parser.parse_args()
    source: Path = args.source

    if not source.is_dir():
        sys.exit(
            f"ERROR: source directory {source} does not exist.\n"
            "Unzip https://www.kaggle.com/datasets/hlrhegemony/pokemon-image-dataset\n"
            "and pass its 'images/' folder via --source."
        )

    folders = sorted(p for p in source.iterdir() if p.is_dir())
    if not folders:
        sys.exit(f"ERROR: no subdirectories under {source} — is this the right path?")

    DEST_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Source: {source} ({len(folders)} pokemon folders)")
    print(f"Dest:   {DEST_DIR}")

    copied = skipped = empty = collisions = 0
    seen: dict[str, str] = {}  # normalized name -> first folder that produced it

    for i, folder in enumerate(folders, 1):
        name = normalize_name(folder.name)
        if not name:
            empty += 1
            continue
        if name in seen:
            print(f"  WARN collision: {folder.name!r} -> {name!r} (already from {seen[name]!r})")
            collisions += 1
            continue
        seen[name] = folder.name

        src = pick_canonical(folder)
        if src is None:
            empty += 1
            continue

        dest = DEST_DIR / f"{name}{src.suffix.lower()}"
        if dest.exists():
            skipped += 1
        else:
            shutil.copyfile(src, dest)
            copied += 1

        if i % BATCH_SIZE == 0:
            print(f"  processed {i}/{len(folders)} (copied {copied}, skipped {skipped})")

    total = len(list(DEST_DIR.glob("*.jpg"))) + len(list(DEST_DIR.glob("*.png")))
    print(
        f"Done. copied {copied}, skipped {skipped}, empty {empty}, collisions {collisions}.\n"
        f"{DEST_DIR} now holds {total} flat images."
    )
    if source.is_relative_to(DEST_DIR):
        print(f"NOTE: source lives inside {DEST_DIR}; remove {source} when satisfied.")


if __name__ == "__main__":
    main()
