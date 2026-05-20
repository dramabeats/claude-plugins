import asyncio
import os
from playwright.async_api import async_playwright, Browser, BrowserContext, Playwright

from tabwright.stealth import random_user_agent, random_viewport

_playwright: Playwright | None = None
_browser: Browser | None = None
_lock = asyncio.Lock()


async def _ensure_browser() -> Browser:
    global _playwright, _browser
    async with _lock:
        if _browser is not None and _browser.is_connected():
            return _browser
        headless = os.getenv("TABWRIGHT_HEADLESS", "false").lower() == "true"
        try:
            _playwright = await async_playwright().start()
            _browser = await _playwright.chromium.launch(headless=headless)
        except Exception:
            if _playwright is not None:
                await _playwright.stop()
                _playwright = None
            raise
        return _browser


async def new_context() -> BrowserContext:
    browser = await _ensure_browser()
    return await browser.new_context(
        user_agent=random_user_agent(),
        viewport=random_viewport(),
    )


async def close_browser() -> None:
    global _browser, _playwright
    try:
        if _browser is not None:
            try:
                await _browser.close()
            finally:
                _browser = None
    finally:
        if _playwright is not None:
            try:
                await _playwright.stop()
            finally:
                _playwright = None
