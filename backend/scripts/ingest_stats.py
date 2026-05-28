#!/usr/bin/env python3
"""One-time ingest: Kaggle Pokemon stats CSV -> shared Turso (libSQL) DB.

Source dataset: https://www.kaggle.com/datasets/abcsds/pokemon (Pokemon.csv,
~800 rows). Place the downloaded file at ``data/raw/Pokemon.csv`` (any *.csv in
data/raw/ is auto-detected). The script never downloads the dataset: it only
processes whatever is already present in data/raw/.

Destination: a Turso database shared by the team, reached over its HTTP
``/v2/pipeline`` endpoint (Hrana protocol). Credentials come from .env:
``TURSO_DATABASE_URL`` (host, no /v2/pipeline suffix) and ``TURSO_AUTH_TOKEN``.

Names are normalized to lowercase for case-insensitive lookups by the POKE
Stats service. The CSV '#' column is stored as ``id`` (Kaggle's per-pokemon ID;
note mega forms share a '#', so ``name`` remains the PRIMARY KEY).

    python scripts/ingest_stats.py
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
BATCH_SIZE = 100

load_dotenv(PROJECT_ROOT / ".env")

# Maps the CSV header (left) to our column (right). The Kaggle file uses these
# exact, space-and-dot headers; '#' is documented as the per-pokemon ID.
COLUMN_MAP = {
    "#": "id",
    "Name": "name",
    "HP": "hp",
    "Attack": "attack",
    "Defense": "defense",
    "Sp. Atk": "sp_atk",
    "Sp. Def": "sp_def",
    "Speed": "speed",
    "Type 1": "type_1",
    "Type 2": "type_2",
    "Total": "total",
    "Generation": "generation",
    "Legendary": "legendary",
}

# Column order used by both CREATE and INSERT.
COLUMNS = [
    "id", "name", "hp", "attack", "defense", "sp_atk", "sp_def",
    "speed", "type_1", "type_2", "total", "generation", "legendary",
]

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS pokemon_stats (
    id          INTEGER,
    name        TEXT PRIMARY KEY,
    hp          INTEGER,
    attack      INTEGER,
    defense     INTEGER,
    sp_atk      INTEGER,
    sp_def      INTEGER,
    speed       INTEGER,
    type_1      TEXT,
    type_2      TEXT,
    total       INTEGER,
    generation  INTEGER,
    legendary   INTEGER
)
"""

INSERT_SQL = (
    "INSERT OR REPLACE INTO pokemon_stats ("
    + ", ".join(COLUMNS)
    + ") VALUES ("
    + ", ".join(["?"] * len(COLUMNS))
    + ")"
)


# --- Turso / Hrana HTTP client --------------------------------------------

def _hrana_value(value: object) -> dict:
    """Wrap a Python scalar as a Hrana typed Value object."""
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "integer", "value": str(int(value))}
    if isinstance(value, int):
        return {"type": "integer", "value": str(value)}
    if isinstance(value, float):
        return {"type": "float", "value": value}
    return {"type": "text", "value": str(value)}


def _config() -> tuple[str, str]:
    base = os.environ.get("TURSO_DATABASE_URL")
    token = os.environ.get("TURSO_AUTH_TOKEN")
    if not base or not token:
        sys.exit(
            "ERROR: TURSO_DATABASE_URL and TURSO_AUTH_TOKEN must be set.\n"
            "Copy .env.example to .env and fill in the shared Turso credentials."
        )
    return base.rstrip("/") + "/v2/pipeline", token


def run_pipeline(client: httpx.Client, url: str, statements: list[tuple[str, list]]) -> list[dict]:
    """Execute a batch of (sql, args) statements in one HTTP pipeline call.

    Returns the per-statement results (excluding the trailing close). Raises if
    any statement reports an error.
    """
    requests = [
        {
            "type": "execute",
            "stmt": {"sql": sql, "args": [_hrana_value(a) for a in args]},
        }
        for sql, args in statements
    ]
    requests.append({"type": "close"})

    resp = client.post(url, json={"requests": requests})
    resp.raise_for_status()
    data = resp.json()

    results = data.get("results", [])
    for res in results:
        if res.get("type") == "error":
            raise RuntimeError(f"Turso statement error: {res.get('error')}")
    return results[:-1]  # drop the close result


def scalar(result: dict) -> object:
    """Extract the first cell of the first row from an execute result."""
    rows = result["response"]["result"]["rows"]
    return rows[0][0].get("value") if rows else None


# --- CSV parsing -----------------------------------------------------------

def find_csv() -> Path:
    preferred = RAW_DIR / "Pokemon.csv"
    if preferred.exists():
        return preferred
    candidates = sorted(RAW_DIR.glob("*.csv"))
    if candidates:
        return candidates[0]
    sys.exit(
        f"ERROR: no CSV found in {RAW_DIR}.\n"
        "Download https://www.kaggle.com/datasets/abcsds/pokemon and place\n"
        f"'Pokemon.csv' in {RAW_DIR}, then re-run this script."
    )


def _to_int(value: str | None) -> int | None:
    value = (value or "").strip()
    if value == "":
        return None
    if value.lower() in ("true", "false"):
        return 1 if value.lower() == "true" else 0
    return int(value)


def parse_row(row: dict[str, str]) -> list:
    record: dict[str, object] = {col: None for col in COLUMNS}
    for csv_col, db_col in COLUMN_MAP.items():
        raw = row.get(csv_col)
        if db_col == "name":
            record["name"] = (raw or "").strip().lower()
        elif db_col in ("type_1", "type_2"):
            record[db_col] = (raw or "").strip() or None
        else:
            record[db_col] = _to_int(raw)
    return [record[col] for col in COLUMNS]


# --- main ------------------------------------------------------------------

def main() -> None:
    csv_path = find_csv()
    url, token = _config()
    print(f"Reading {csv_path}")
    print(f"Target: {url}")

    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client(headers=headers, timeout=30) as client:
        run_pipeline(client, url, [(CREATE_SQL, [])])
        print("Table pokemon_stats ready.")

        with csv_path.open(encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            missing = set(COLUMN_MAP) - set(reader.fieldnames or [])
            if missing:
                sys.exit(f"ERROR: CSV is missing expected columns: {sorted(missing)}")

            batch: list[tuple[str, list]] = []
            total = 0
            for row in reader:
                args = parse_row(row)
                if not args[COLUMNS.index("name")]:
                    continue
                batch.append((INSERT_SQL, args))
                if len(batch) >= BATCH_SIZE:
                    run_pipeline(client, url, batch)
                    total += len(batch)
                    print(f"  inserted batch -> {total} rows so far")
                    batch.clear()
            if batch:
                run_pipeline(client, url, batch)
                total += len(batch)
                print(f"  inserted final batch -> {total} rows")

        count = scalar(run_pipeline(client, url, [("SELECT COUNT(*) FROM pokemon_stats", [])])[0])
        print(f"Done. pokemon_stats now holds {count} pokemon.")


if __name__ == "__main__":
    main()
