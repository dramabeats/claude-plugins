from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from tabwright.browser import close_browser
from tabwright.fetcher import fetch_page as _fetch_generic
from tabwright.reddit import fetch_reddit as _fetch_reddit
from tabwright.search import web_search as _web_search
from tabwright import tabs as _tabs


@asynccontextmanager
async def lifespan(server):
    """Ensure the browser is closed cleanly when the MCP server shuts down."""
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
        return await _fetch_reddit(url)
    return await _fetch_generic(url)


@mcp.tool()
async def open_tab(name: str) -> dict:
    """Open a new named browser tab. Error if name already exists."""
    return await _tabs.open_tab(name)


@mcp.tool()
async def navigate(name: str, url: str) -> dict:
    """Navigate a named tab to a URL. Returns {name, url, title}."""
    return await _tabs.navigate(name, url)


@mcp.tool()
async def snapshot(name: str) -> dict:
    """Get an ARIA snapshot of a named tab. Returns {name, url, snapshot}."""
    return await _tabs.snapshot(name)


@mcp.tool()
async def click(name: str, ref: str) -> dict:
    """Click an element in a named tab.

    `ref` is an accessible name as shown in snapshot() -- button/link text,
    aria-label, placeholder or title all work -- or a CSS/XPath selector.
    Returns {name, url}."""
    return await _tabs.click(name, ref)


@mcp.tool()
async def type_text(name: str, ref: str, text: str) -> dict:
    """Type text into a named tab element.

    `ref` is an accessible name as shown in snapshot() -- aria-label,
    placeholder or title all work -- or a CSS/XPath selector.
    Returns {name, url}."""
    return await _tabs.type_text(name, ref, text)


@mcp.tool()
async def close_tab(name: str) -> dict:
    """Close a named browser tab. Returns {name, closed: true}."""
    return await _tabs.close_tab(name)


@mcp.tool()
async def list_tabs() -> dict:
    """List all open named tabs. Returns {tabs: {name: current_url}}."""
    return await _tabs.list_tabs()


if __name__ == "__main__":
    mcp.run()
