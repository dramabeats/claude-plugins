---
name: tabshots-setup
description: Guided setup for tabshots — configure watch directory and cloud storage provider
argument-hint: [provider]
allowed-tools: [Bash, Read, Edit]
---

# tabshots Setup

Walk the user through configuring their screenshot watch directory. Update `config.json` in the plugin root when done. Tell the user to restart Claude Code when finished so the MCP server picks up the new config.

## Step 1: Find the plugin root

Run:
```bash
echo "${CLAUDE_PLUGIN_ROOT}"
```

Record the printed path — call it PLUGIN_ROOT. Use the literal value in all subsequent commands (do not rely on the shell variable expanding it inside heredocs or strings).

## Step 2: Ask for provider (if not given as argument)

Ask the user which provider their screenshots come from:

1. **Google Drive** (via rclone)
2. **ownCloud / Nextcloud** (via rclone WebDAV)
3. **Local folder** (already mounted or just a local path)

## Step 3a: Google Drive setup

Check if rclone is installed:
```bash
which rclone || echo "NOT FOUND"
```

If not found, tell the user:
> Install rclone first: `sudo apt install rclone` (Debian/Ubuntu) or `sudo pacman -S rclone` (Arch), then re-run `/tabshots-setup`.

Check existing remotes:
```bash
rclone listremotes
```

If a `gdrive:` remote already exists, skip to Step 3a-mount.

If not, guide the user through headless rclone config:
> Run `! rclone config` in the prompt. Choose: new remote → name it `gdrive` → type `drive` → leave Client ID/Secret blank → scope `1` (full access) → advanced config `n` → auto config `n`. rclone will print a URL — open it on any device with a browser, sign in, paste the verification code back.

**Step 3a-mount:** Ask the user for the mount point (default: `~/gdrive`). Then set up a systemd user service:

```bash
MOUNT_POINT="$HOME/gdrive"   # or user-specified path
mkdir -p "$MOUNT_POINT"

cat > ~/.config/systemd/user/rclone-gdrive.service << EOF
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

Ask the user for the screenshots subfolder within the mount (e.g. `Screenshots`, `Pictures/Screenshots`). Compose the full watch_dir: `~/gdrive/<subfolder>`.

Verify the path is accessible:
```bash
ls "$MOUNT_POINT/<subfolder>" | head -3
```

## Step 3b: ownCloud / Nextcloud setup

Ask for:
- Server URL (e.g. `https://cloud.example.com`)
- Username
- Password (will be stored by rclone config)

Guide through rclone WebDAV config:
> Run `! rclone config`. Choose: new remote → name it `nextcloud` (or `owncloud`) → type `webdav` → URL: `<server>/remote.php/dav/files/<username>` → vendor: `nextcloud` or `owncloud` → username and password as provided.

Then set up mount (same systemd pattern as Google Drive, substituting the remote name and mount point). Ask for screenshots subfolder. Compose watch_dir.

## Step 3c: Local folder

Ask for the absolute path (or `~`-prefixed path) of the screenshots folder.

Verify it exists:
```bash
ls "<path>" | head -3
```

## Step 4: Write config

Use the literal PLUGIN_ROOT path recorded in Step 1 (substitute it into the command below):

```bash
/path/to/plugin/venv/bin/python -c "
import sys
sys.path.insert(0, '/path/to/plugin')
from tabshots.config import save_config
save_config({'watch_dir': '<resolved_watch_dir>'})
print('Config updated.')
"
```

Replace `/path/to/plugin` with the actual PLUGIN_ROOT value from Step 1, and `<resolved_watch_dir>` with the full expanded path determined in Step 3.

## Step 5: Confirm and instruct restart

Tell the user:
> Config saved. **Restart Claude Code** so the tabshots MCP server picks up the new watch directory. After restarting, take a screenshot and type "screenshot" in any prompt to test.
