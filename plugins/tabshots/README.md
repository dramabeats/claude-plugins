# tabshots

Watches your screenshot folder, runs OCR, and lets Claude Code examine your latest screenshot when you type "screenshot" in a prompt.

## Requirements

- Python 3.9+
- `tesseract-ocr` system package
- `rclone` (for Google Drive sync)

```bash
sudo apt install tesseract-ocr rclone   # Debian/Ubuntu
sudo pacman -S tesseract rclone         # Arch
```

## Install

```bash
./install.sh
```

This will:
1. Install Python dependencies (`watchdog`, `pytesseract`, `Pillow`)
2. Register the Claude Code hook in `~/.claude/settings.json`
3. Start `tabshots-watcher` as a systemd user service (survives reboots)

## Google Drive setup

tabshots works with any local folder, including rclone-mounted Google Drive.

**1. Configure rclone (headless — no browser needed on this machine):**
```bash
rclone config
```
Follow the prompts: new remote → name `gdrive` → type `drive` → leave Client ID/Secret blank → scope `1` → advanced config `n` → **auto config `n`**.

rclone prints a URL. Open it on any device with a browser (phone, laptop), sign in to Google, and paste the verification code back into the terminal.

**2. Mount Google Drive:**
```bash
mkdir -p ~/gdrive
```

**3. Set up persistent mount (systemd):**
```bash
cat > ~/.config/systemd/user/rclone-gdrive.service << 'EOF'
[Unit]
Description=rclone Google Drive mount
After=default.target

[Service]
Type=notify
ExecStart=/usr/bin/rclone mount gdrive: %h/gdrive --vfs-cache-mode full --vfs-cache-max-age 10m --dir-cache-time 5m --poll-interval 30s
ExecStop=/bin/fusermount -u %h/gdrive
Restart=on-failure

[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now rclone-gdrive
```

**4. Update `config.json`:**
```json
{
  "watch_dir": "~/gdrive/Pictures/Screenshots",
  "tesseract_lang": "eng",
  "tesseract_psm": 3
}
```

## Configuration

Edit `config.json` in the repo root:

| Field | Default | Description |
|-------|---------|-------------|
| `watch_dir` | `~/Pictures/Screenshots` | Directory to watch for new screenshots |
| `tesseract_lang` | `eng` | Tesseract language code |
| `tesseract_psm` | `3` | Page segmentation mode (3 = auto) |

`watch_dir` supports `~` and environment variables.

## Usage

Take a screenshot. Then in Claude Code, include "screenshot" anywhere in your prompt:

> "Can you check the screenshot and tell me what that error says?"

Claude will automatically read the latest screenshot.

## Service management

```bash
systemctl --user status tabshots-watcher    # check status
systemctl --user restart tabshots-watcher   # restart after config change
journalctl --user -u tabshots-watcher -f    # live logs
```

## Run tests

```bash
pytest -v
bash tests/test_hook.sh
```
