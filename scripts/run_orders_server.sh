#!/usr/bin/env bash
# Starts the orders MCP server. Creates a private virtual environment on first run,
# because the MCP SDK needs Python 3.10 or newer and a plugin cannot ship a .venv.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${HR_DESK_VENV:-$HOME/.cache/halden-reed-desk/venv}"
if [ ! -x "$VENV/bin/python" ]; then
  PY=""
  for c in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
      PY="$c"; break
    fi
  done
  if [ -z "$PY" ]; then
    echo "halden-reed-desk: the orders server needs Python 3.10 or newer, none found." >&2
    exit 1
  fi
  "$PY" -m venv "$VENV" >&2
  "$VENV/bin/pip" install -q -r "$ROOT/requirements.txt" >&2
fi
exec "$VENV/bin/python" "$ROOT/mcp_servers/orders/server.py"
