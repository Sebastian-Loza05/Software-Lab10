#!/usr/bin/env bash
# Stop the 4 PokeSearch microservices started by start_all.sh.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT/.run"

for name in poke_api poke_stats poke_images search_api; do
  pidfile="$RUN_DIR/${name}.pid"
  if [ -f "$pidfile" ]; then
    pid="$(cat "$pidfile")"
    if kill "$pid" 2>/dev/null; then
      echo "  stopped ${name} (pid ${pid})"
    fi
    rm -f "$pidfile"
  fi
done

# Safety net: kill any stray uvicorn for these apps.
pkill -f "main:app --app-dir services" 2>/dev/null || true
echo "done."
