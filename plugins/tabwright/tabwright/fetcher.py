from bs4 import BeautifulSoup
from markdownify import markdownify
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from tabwright.browser import new_context
from tabwright.stealth import random_delay

_STRIP_TAGS = ["nav", "header", "footer", "aside", "script", "style", "noscript"]


def html_to_markdown(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(_STRIP_TAGS):
        tag.decompose()
    main = soup.find("main") or soup.find("article") or soup.find("body") or soup
    return markdownify(str(main), heading_style="ATX").strip()


async def fetch_page(url: str) -> dict:
    context = await new_context()
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await random_delay(0.5, 1.5)
        html = await page.content()
        content = html_to_markdown(html)
        return {"url": url, "content": content, "content_type": "generic"}
    except PlaywrightTimeoutError:
        return {"url": url, "content": "", "content_type": "generic", "error": "timeout"}
    except Exception:
        return {"url": url, "content": "", "content_type": "generic", "error": "blocked"}
    finally:
        await page.close()
        await context.close()
