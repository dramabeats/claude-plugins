from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from tabwright.browser import close_browser, new_context
from tabwright.fetcher import fetch_page as _fetch_generic
from tabwright.reddit import extract_reddit
from tabwright.search import web_search as _web_search
from tabwright.stealth import random_delay


@asynccontextmanager
async def lifespan(server):
    try:
        yield
    finally:
        await close_browser()


mcp = FastMCP("tabwright", lifespan=lifespan)


@mcp.tool()
async def web_search(
    query: str,
    prefer_reddit: bool = False,
    max_results: int = 10,
) -> list[dict]:
    """Search the web via DuckDuckGo. Returns list of {title, url, snippet}.
    Set prefer_reddit=True to bubble Reddit results to the top."""
    return await _web_search(query, prefer_reddit=prefer_reddit, max_results=max_results)


@mcp.tool()
async def fetch_page(url: str) -> dict:
    """Fetch a web page and return clean markdown content.
    Automatically uses Reddit-optimised extraction for reddit.com URLs.
    Returns {url, content, content_type} or {url, content, content_type, error} on failure."""
    if "reddit.com" in url:
        context = await new_context()
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await random_delay()
            html = await page.content()
            return extract_reddit(html, url)
        except PlaywrightTimeoutError:
            return {"url": url, "content": "", "content_type": "reddit", "error": "timeout"}
        except Exception:
            return {"url": url, "content": "", "content_type": "reddit", "error": "blocked"}
        finally:
            await page.close()
            await context.close()
    return await _fetch_generic(url)


if __name__ == "__main__":
    mcp.run()
