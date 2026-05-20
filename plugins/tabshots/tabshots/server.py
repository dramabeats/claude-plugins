import threading
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from tabshots.config import load_config
from tabshots.watcher import start_watcher

_latest: dict = {}
_lock = threading.Lock()


def _on_processed(payload: dict) -> None:
    with _lock:
        _latest.clear()
        _latest.update(payload)


@asynccontextmanager
async def lifespan(server):
    cfg = load_config()
    observer = start_watcher(cfg, on_processed=_on_processed)
    try:
        yield
    finally:
        observer.stop()
        observer.join()


mcp = FastMCP("tabshots", lifespan=lifespan)


@mcp.tool()
def get_latest_screenshot() -> dict:
    """Return path, OCR text, and timestamp of the most recent screenshot."""
    with _lock:
        return dict(_latest)


if __name__ == "__main__":
    mcp.run()
