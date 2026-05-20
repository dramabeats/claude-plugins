#!/usr/bin/env bash
set -euo pipefail
PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$PLUGIN_ROOT/venv/bin/python"
if [[ ! -f "$VENV_PYTHON" ]]; then
    echo "tabwright: first run — creating venv..." >&2
    python3 -m venv "$PLUGIN_ROOT/venv"
    "$VENV_PYTHON" -m pip install -r "$PLUGIN_ROOT/requirements.txt" --quiet >&2
    "$VENV_PYTHON" -m camoufox fetch >&2
    echo "tabwright: venv ready." >&2
fi
export PYTHONPATH="$PLUGIN_ROOT"
exec "$VENV_PYTHON" -m tabwright.server
