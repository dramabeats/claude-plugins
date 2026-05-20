import logging
from urllib.parse import urlencode

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from tabwright.browser import new_context
from tabwright.stealth import random_delay

logger = logging.getLogger(__name__)

# kl=us-en sets DuckDuckGo locale to US English for consistent result structure
_DDG_LOCALE = "us-en"

# Try multiple selectors in order — DDG occasionally changes their DOM
_RESULT_SELECTORS = [
    '[data-testid="result"]',
    "article.result",
    ".results .result",
]


async def web_search(
    query: str,
    prefer_reddit: bool = False,
    max_results: int = 10,
) -> list[dict]:
    params = urlencode({"q": query, "kl": _DDG_LOCALE})
    url = f"https://duckduckgo.com/?{params}"

    context = await new_context()
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await random_delay()

        selector_list = ", ".join(f"'{s}'" for s in _RESULT_SELECTORS)
        results = await page.evaluate(f"""
            () => {{
                const selectors = [{selector_list}];
                let items = [];
                for (const sel of selectors) {{
                    const found = document.querySelectorAll(sel);
                    if (found.length > 0) {{ items = Array.from(found); break; }}
                }}
                return items.map(item => ({{
                    title: (item.querySelector('h2') || {{}}).innerText || '',
                    url: (item.querySelector('a[data-testid="result-title-a"]') || item.querySelector('a[href]') || {{}}).href || '',
                    snippet: (item.querySelector('[data-result="snippet"]') || item.querySelector('p') || {{}}).innerText || '',
                }})).filter(r => r.url !== '' && r.url.startsWith('http'));
            }}
        """)

        results = results[:max_results]

        if prefer_reddit:
            reddit_results = [r for r in results if "reddit.com" in r.get("url", "")]
            other_results = [r for r in results if "reddit.com" not in r.get("url", "")]
            results = reddit_results + other_results

        return results
    except PlaywrightTimeoutError:
        logger.warning("web_search timed out for query: %s", query)
        return []
    except Exception:
        logger.exception("web_search failed for query: %s", query)
        return []
    finally:
        await page.close()
        await context.close()
