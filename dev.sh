#!/usr/bin/env bash
# Run the Aurora Hub backend (FastAPI) and frontend (Next.js) together.
# Ctrl+C stops both. Logs are interleaved in this terminal.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

port_is_free() {
  python3 - "$1" <<'PY' >/dev/null 2>&1
import socket
import sys

port = int(sys.argv[1])
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("127.0.0.1", port))
    except OSError:
        raise SystemExit(1)
PY
}

pick_frontend_port() {
  local port="$1"
  while ! port_is_free "$port"; do
    port=$((port + 1))
  done
  printf '%s' "$port"
}

REQUESTED_FRONTEND_PORT="$FRONTEND_PORT"
FRONTEND_PORT="$(pick_frontend_port "$REQUESTED_FRONTEND_PORT")"

pids=()
cleanup() {
  echo
  echo "Shutting down…"
  for pid in "${pids[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

# --- Backend ---------------------------------------------------------------
if [[ ! -d "$ROOT/backend/.venv" ]]; then
  echo "backend/.venv not found. Create it first:" >&2
  echo "  cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -e '.[dev]'" >&2
  exit 1
fi

echo "Starting backend on http://localhost:$BACKEND_PORT (docs at /docs)…"
(
  cd "$ROOT/backend"
  source .venv/bin/activate
  exec uvicorn app.main:app --reload --port "$BACKEND_PORT"
) &
pids+=($!)

# --- Frontend --------------------------------------------------------------
if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  echo "frontend/node_modules not found. Run: cd frontend && npm install" >&2
  exit 1
fi

if [[ "$FRONTEND_PORT" != "$REQUESTED_FRONTEND_PORT" ]]; then
  echo "Frontend port $REQUESTED_FRONTEND_PORT is busy; using $FRONTEND_PORT instead."
fi
echo "Starting frontend on http://localhost:$FRONTEND_PORT…"
(
  cd "$ROOT/frontend"
  exec npm run dev -- --port "$FRONTEND_PORT"
) &
pids+=($!)

# Wait for either process to exit; cleanup trap stops the other.
wait -n
