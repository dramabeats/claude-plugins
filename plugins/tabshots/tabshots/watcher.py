import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Callable, Optional

import pytesseract
from PIL import Image
from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver

from tabshots.config import LATEST_PATH, load_config

_IMAGE_EXTS = {".png", ".jpg", ".jpeg"}


def ocr_image(image_path: str, lang: str, psm: int) -> str:
    with Image.open(image_path) as img:
        dpi = img.info.get("dpi")
        current_dpi = dpi[0] if isinstance(dpi, (tuple, list)) else (dpi or 72)
        if current_dpi < 300:
            scale = 300 / current_dpi
            new_size = (int(img.width * scale), int(img.height * scale))
            img = img.resize(new_size, Image.LANCZOS)
        return pytesseract.image_to_string(img, lang=lang, config=f"--psm {psm}")


def process_screenshot(path: str, lang: str, psm: int) -> Optional[dict]:
    try:
        text = ocr_image(path, lang=lang, psm=psm)
    except Exception as exc:
        print(f"OCR failed for {path}: {exc}", file=sys.stderr)
        return None

    timestamp = datetime.now(timezone.utc).isoformat()
    payload = {"path": path, "text": text, "timestamp": timestamp}

    sidecar = path + ".ocr.json"
    with open(sidecar, "w") as f:
        json.dump(payload, f)

    tmp = str(LATEST_PATH) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f)
    os.replace(tmp, LATEST_PATH)

    print(f"Processed: {path}", file=sys.stderr)
    return payload


class ScreenshotHandler(FileSystemEventHandler):
    def __init__(self, lang: str, psm: int, on_processed: Optional[Callable[[dict], None]] = None):
        self.lang = lang
        self.psm = psm
        self.on_processed = on_processed

    def on_created(self, event):
        if event.is_directory:
            return
        path: str = event.src_path
        suffix = os.path.splitext(path)[1].lower()
        if suffix not in _IMAGE_EXTS:
            return
        time.sleep(0.5)
        payload = process_screenshot(path, lang=self.lang, psm=self.psm)
        if payload is not None and self.on_processed is not None:
            self.on_processed(payload)


def start_watcher(cfg: dict, on_processed: Optional[Callable[[dict], None]] = None) -> PollingObserver:
    handler = ScreenshotHandler(lang=cfg["tesseract_lang"], psm=cfg["tesseract_psm"], on_processed=on_processed)
    poll_interval = cfg.get("poll_interval", 1)
    observer = PollingObserver(timeout=poll_interval)
    observer.schedule(handler, cfg["watch_dir"], recursive=False)
    observer.start()
    return observer


def watch() -> None:
    cfg = load_config()
    print(f"Watching {cfg['watch_dir']}...", file=sys.stderr)
    observer = start_watcher(cfg)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    watch()
