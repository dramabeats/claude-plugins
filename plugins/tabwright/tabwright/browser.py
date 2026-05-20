import asyncio
import os
from camoufox.async_api import AsyncCamoufox
from playwright.async_api import Browser, BrowserContext

_camoufox: AsyncCamoufox | None = None
_browser: Browser | None = None
_lock = asyncio.Lock()


async def _ensure_browser() -> Browser:
    global _camoufox, _browser
    async with _lock:
        if _browser is not None and _browser.is_connected():
            return _browser
        headless = os.getenv("TABWRIGHT_HEADLESS", "false").lower() == "true"
        try:
            _camoufox = AsyncCamoufox(headless=headless)
            _browser = await _camoufox.__aenter__()
        except Exception:
            if _camoufox is not None:
                await _camoufox.__aexit__(None, None, None)
                _camoufox = None
            raise
        return _browser


async def new_context() -> BrowserContext:
    # Camoufox randomises fingerprint, UA, and viewport automatically
    browser = await _ensure_browser()
    return await browser.new_context()


async def close_browser() -> None:
    global _camoufox, _browser
    try:
        if _camoufox is not None:
            await _camoufox.__aexit__(None, None, None)
    finally:
        _camoufox = None
        _browser = None
