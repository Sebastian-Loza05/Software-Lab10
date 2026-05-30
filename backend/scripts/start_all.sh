#!/usr/bin/env bash
# Launch the 4 PokeSearch microservices in the background.
# Usage:  ./scripts/start_all.sh
# Stop:   ./scripts/stop_all.sh   (or kill the PIDs printed below)
set -euo pipefail

# Project root = the backend/ dir that contains services/ and this scripts/ dir.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Pick the virtualenv (the team uses env/; fall back to .venv).
if [ -x env/bin/uvicorn ]; then
  UVICORN="env/bin/uvicorn"
elif [ -x .venv/bin/uvicorn ]; then
  UVICORN=".venv/bin/uvicorn"
else
  echo "ERROR: uvicorn not found. Create a venv and 'pip install -r requirements.txt'." >&2
  exit 1
fi

RUN_DIR="$ROOT/.run"
mkdir -p "$RUN_DIR"

start() {  # name  port
  local name="$1" port="$2"
  setsid "$UVICORN" "${name}.main:app" --app-dir services --port "$port" \
    --log-level warning >"$RUN_DIR/${name}.log" 2>&1 < /dev/null &
  echo $! > "$RUN_DIR/${name}.pid"
  echo "  ${name}  ->  http://localhost:${port}   (pid $!)"
}

echo "Starting services (logs in $RUN_DIR/, request logs in logs/):"
start poke_api    8001
start poke_stats  8002
start poke_images 8003
start search_api  8000

echo
echo "Waiting for /health on all services..."
for port in 8001 8002 8003 8000; do
  if curl -s --retry 20 --retry-delay 1 --retry-all-errors --retry-connrefused -m 3 \
       "http://localhost:${port}/health" >/dev/null; then
    echo "  port ${port}: UP"
  else
    echo "  port ${port}: DOWN — check $RUN_DIR/*.log" >&2
  fi
done
echo
echo "Gateway ready:  POST http://localhost:8000/poke/search"
