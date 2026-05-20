from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from tabwright.browser import close_browser
from tabwright.fetcher import fetch_page as _fetch_generic
from tabwright.reddit import fetch_reddit as _fetch_reddit
from tabwright.search import web_search as _web_search


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


if __name__ == "__main__":
    mcp.run()
