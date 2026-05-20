#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== tabshots installer ==="

# 1. Check tesseract
if ! command -v tesseract &>/dev/null; then
    echo "ERROR: tesseract not found. Install it first:"
    echo "  Ubuntu/Debian: sudo apt install tesseract-ocr"
    echo "  Arch:          sudo pacman -S tesseract"
    exit 1
fi
echo "tesseract: $(tesseract --version 2>&1 | head -1)"

# 2. Install Python deps into a venv
echo "Setting up Python virtual environment..."
python3 -m venv "$SCRIPT_DIR/venv"
"$SCRIPT_DIR/venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" --quiet
echo "Python dependencies installed."

# 3. Make scripts executable
chmod +x "$SCRIPT_DIR/hooks/screenshot.sh"
chmod +x "$SCRIPT_DIR/run-server.sh"

# 4. Disable old systemd service if it exists (migrating from previous install)
if systemctl --user is-enabled tabshots-watcher.service &>/dev/null; then
    echo "Disabling old tabshots-watcher systemd service..."
    systemctl --user disable --now tabshots-watcher.service || true
    rm -f "$HOME/.config/systemd/user/tabshots-watcher.service"
    systemctl --user daemon-reload
    echo "Old service removed."
fi

echo ""
echo "=== tabshots installed. ==="
echo "Run /plugin install to activate, then restart Claude Code."
echo "Run /tabshots-setup to configure your watch directory."
