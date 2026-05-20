from urllib.parse import urlencode

from tabwright.browser import new_context
from tabwright.stealth import random_delay


async def web_search(
    query: str,
    prefer_reddit: bool = False,
    max_results: int = 10,
) -> list[dict]:
    params = urlencode({"q": query, "kl": "us-en"})
    url = f"https://duckduckgo.com/?{params}"

    context = await new_context()
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await random_delay()

        results = await page.evaluate("""
            () => {
                const items = document.querySelectorAll('[data-testid="result"]');
                return Array.from(items).map(item => ({
                    title: (item.querySelector('h2') || {}).innerText || '',
                    url: (item.querySelector('a[data-testid="result-title-a"]') || {}).href || '',
                    snippet: (item.querySelector('[data-result="snippet"]') || {}).innerText || '',
                })).filter(r => r.url !== '');
            }
        """)

        results = results[:max_results]

        if prefer_reddit:
            reddit_results = [r for r in results if "reddit.com" in r.get("url", "")]
            other_results = [r for r in results if "reddit.com" not in r.get("url", "")]
            results = reddit_results + other_results

        return results
    except Exception:
        return []
    finally:
        await page.close()
        await context.close()
