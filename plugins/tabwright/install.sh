#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== tabwright installer ==="

echo "Setting up Python virtual environment..."
python3 -m venv "$SCRIPT_DIR/venv"
"$SCRIPT_DIR/venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" --quiet
echo "Python dependencies installed."

echo "Installing Camoufox browser (Firefox)..."
"$SCRIPT_DIR/venv/bin/python" -m camoufox fetch
echo "Camoufox ready."

chmod +x "$SCRIPT_DIR/run-server.sh"

echo ""
echo "=== tabwright installed. ==="
echo "Run /plugin install to activate, then restart Claude Code."
