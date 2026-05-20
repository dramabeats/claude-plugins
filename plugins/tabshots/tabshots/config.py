import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CONFIG_PATH = REPO_ROOT / "config.json"
LATEST_PATH = REPO_ROOT / "latest.json"

_DEFAULTS = {
    "watch_dir": "~/Pictures/Screenshots",
    "tesseract_lang": "eng",
    "tesseract_psm": 3,
    "poll_interval": 1,
}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        cfg = dict(_DEFAULTS)
    else:
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
        for key, val in _DEFAULTS.items():
            cfg.setdefault(key, val)

    cfg["watch_dir"] = os.path.expandvars(os.path.expanduser(cfg["watch_dir"]))
    return cfg


def save_config(updates: dict) -> None:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
    else:
        cfg = {}
    cfg.update(updates)
    tmp = str(CONFIG_PATH) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(cfg, f, indent=2)
    os.replace(tmp, CONFIG_PATH)
