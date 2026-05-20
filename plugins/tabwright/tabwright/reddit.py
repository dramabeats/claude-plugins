from bs4 import BeautifulSoup
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from tabwright.browser import new_context
from tabwright.stealth import random_delay


async def fetch_reddit(url: str) -> dict:
    """Fetch a Reddit page with Playwright and return extracted post+comment markdown."""
    context = await new_context()
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await random_delay(0.5, 1.5)
        html = await page.content()
        return extract_reddit(html, url)
    except PlaywrightTimeoutError:
        return {"url": url, "content": "", "content_type": "reddit", "error": "timeout"}
    except Exception:
        return {"url": url, "content": "", "content_type": "reddit", "error": "blocked"}
    finally:
        await page.close()
        await context.close()


def extract_reddit(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    title_el = soup.find("h1")
    title = title_el.get_text(strip=True) if title_el else "Unknown Post"

    post_el = soup.find("shreddit-post")
    score = post_el.get("score", "?") if post_el else "?"
    author = post_el.get("author", "unknown") if post_el else "unknown"

    body_el = soup.find("div", {"slot": "text-body"})
    body = body_el.get_text(strip=True) if body_el else ""

    comments = []
    for comment in soup.select("shreddit-comment"):
        c_author = comment.get("author", "unknown")
        c_score = comment.get("score", "?")
        c_body = comment.find("div", {"slot": "comment"})
        c_text = c_body.get_text(strip=True) if c_body else ""
        if c_text:
            comments.append(f"**{c_author}** (score: {c_score})\n{c_text}")

    parts = [
        f"# {title}",
        f"**Score:** {score} | **Author:** {author}",
        "",
        body,
        "",
        "## Comments",
        "",
        *comments,
    ]

    return {
        "url": url,
        "content": "\n".join(parts),
        "content_type": "reddit",
    }
