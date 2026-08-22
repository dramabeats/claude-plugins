import asyncio
import logging
import os

from camoufox.async_api import AsyncCamoufox
from playwright.async_api import Browser, BrowserContext, Page

logger = logging.getLogger(__name__)

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


class TabRegistry:
    """Long-lived named tabs, each in its own context.

    web_search and fetch_page open a context per call and throw it away.
    Tabs are the opposite: the caller names one, keeps it across tool calls,
    and closes it when done.
    """

    def __init__(self) -> None:
        self._tabs: dict[str, tuple[BrowserContext, Page]] = {}
        self._lock = asyncio.Lock()

    async def open(self, name: str) -> Page:
        async with self._lock:
            if name in self._tabs:
                raise ValueError(f"Tab '{name}' already exists")
            context = await new_context()
            page = await context.new_page()
            self._tabs[name] = (context, page)
            return page

    async def get(self, name: str) -> Page:
        if name not in self._tabs:
            raise ValueError(f"Tab '{name}' not found")
        return self._tabs[name][1]

    async def close(self, name: str) -> None:
        if name not in self._tabs:
            raise ValueError(f"Tab '{name}' not found")
        context, page = self._tabs.pop(name)
        await page.close()
        await context.close()

    def list(self) -> dict[str, str]:
        return {name: page.url for name, (_, page) in self._tabs.items()}

    async def close_all(self) -> None:
        for name in list(self._tabs):
            try:
                await self.close(name)
            except Exception as e:
                logger.warning("Error closing tab %r: %s", name, e)


tabs = TabRegistry()


async def close_browser() -> None:
    global _camoufox, _browser
    try:
        await tabs.close_all()
        if _camoufox is not None:
            await _camoufox.__aexit__(None, None, None)
    finally:
        _camoufox = None
        _browser = None
