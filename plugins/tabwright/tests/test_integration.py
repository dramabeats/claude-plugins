import os
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("TABWRIGHT_SKIP_INTEGRATION", "false").lower() == "true",
    reason="Integration tests skipped (TABWRIGHT_SKIP_INTEGRATION=true)",
)


@pytest.fixture(autouse=True)
def set_headless(monkeypatch):
    monkeypatch.setenv("TABWRIGHT_HEADLESS", "true")


@pytest.mark.xfail(strict=False, reason="DuckDuckGo may block server IPs; pass when unblocked")
@pytest.mark.asyncio
async def test_web_search_returns_results():
    from tabwright.search import web_search
    from tabwright.browser import close_browser

    try:
        results = await web_search("python list reversal", max_results=5)
        assert isinstance(results, list)
        assert len(results) > 0
        first = results[0]
        assert "title" in first
        assert "url" in first
        assert "snippet" in first
        assert first["url"].startswith("http")
    finally:
        await close_browser()


@pytest.mark.asyncio
async def test_web_search_prefer_reddit_bubbles_reddit():
    from tabwright.search import web_search
    from tabwright.browser import close_browser

    try:
        results = await web_search("python list reversal site:reddit.com", prefer_reddit=True, max_results=10)
        assert isinstance(results, list)
        if len(results) > 1:
            reddit_results = [r for r in results if "reddit.com" in r["url"]]
            if reddit_results:
                assert results[0]["url"] == reddit_results[0]["url"]
    finally:
        await close_browser()


@pytest.mark.asyncio
async def test_fetch_page_generic_returns_markdown():
    from tabwright.fetcher import fetch_page
    from tabwright.browser import close_browser

    try:
        result = await fetch_page("https://example.com")
        assert result["content_type"] == "generic"
        assert "Example Domain" in result["content"]
        assert result["url"] == "https://example.com"
        assert "error" not in result
    finally:
        await close_browser()


@pytest.mark.asyncio
async def test_fetch_page_timeout_returns_error():
    from tabwright.fetcher import fetch_page
    from tabwright.browser import close_browser

    try:
        # Non-routable IP to force timeout
        result = await fetch_page("http://192.0.2.1/")
        assert "error" in result
        assert result["error"] in ("timeout", "blocked")
    finally:
        await close_browser()
