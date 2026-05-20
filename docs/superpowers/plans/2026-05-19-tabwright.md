# Tabwright Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code MCP plugin called `tabwright` that gives Claude a human-like Playwright browser for web research via two tools: `web_search` and `fetch_page`.

**Architecture:** Python FastMCP server with a singleton Playwright browser. `web_search` hits DuckDuckGo and returns ranked results; `fetch_page` fetches a URL and returns clean markdown, with a Reddit-specific extractor for JS-rendered post+comment content. Stealth helpers (random UA, delay, viewport) are shared across both tools.

**Tech Stack:** Python 3.11+, Playwright (chromium), FastMCP (`mcp>=1.0.0`), BeautifulSoup4, markdownify, pytest

---

## File Map

```
plugins/tabwright/
├── .claude-plugin/plugin.json     # plugin manifest
├── .mcp.json                      # MCP server config
├── install.sh                     # one-time setup (venv + playwright install)
├── run-server.sh                  # MCP entry point (auto-creates venv)
├── requirements.txt               # Python deps
├── tabwright/
│   ├── __init__.py
│   ├── server.py                  # FastMCP tool registration
│   ├── browser.py                 # singleton Playwright browser/context
│   ├── stealth.py                 # UA rotation, delay, viewport helpers
│   ├── search.py                  # DuckDuckGo scraping + Reddit reranking
│   ├── fetcher.py                 # generic HTML → markdown
│   └── reddit.py                  # Reddit-specific post+comment extractor
└── tests/
    ├── __init__.py
    ├── fixtures/
    │   └── reddit_post.html       # saved Reddit HTML for unit tests
    ├── test_stealth.py
    ├── test_fetcher.py
    ├── test_reddit.py
    └── test_integration.py        # real-browser tests (skipped without display)
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `plugins/tabwright/requirements.txt`
- Create: `plugins/tabwright/run-server.sh`
- Create: `plugins/tabwright/install.sh`
- Create: `plugins/tabwright/.mcp.json`
- Create: `plugins/tabwright/.claude-plugin/plugin.json`
- Create: `plugins/tabwright/tabwright/__init__.py`
- Create: `plugins/tabwright/tests/__init__.py`
- Create: `plugins/tabwright/tests/fixtures/` (empty dir placeholder)

- [ ] **Step 1: Create the directory structure**

```bash
mkdir -p /home/caleb/claude-plugins/plugins/tabwright/.claude-plugin
mkdir -p /home/caleb/claude-plugins/plugins/tabwright/tabwright
mkdir -p /home/caleb/claude-plugins/plugins/tabwright/tests/fixtures
touch /home/caleb/claude-plugins/plugins/tabwright/tabwright/__init__.py
touch /home/caleb/claude-plugins/plugins/tabwright/tests/__init__.py
```

- [ ] **Step 2: Write `requirements.txt`**

```
mcp>=1.0.0
playwright>=1.44.0
beautifulsoup4>=4.12.0
markdownify>=0.12.1
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

- [ ] **Step 3: Write `run-server.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$PLUGIN_ROOT/venv/bin/python"
if [[ ! -f "$VENV_PYTHON" ]]; then
    echo "tabwright: first run — creating venv..." >&2
    python3 -m venv "$PLUGIN_ROOT/venv"
    "$VENV_PYTHON" -m pip install -r "$PLUGIN_ROOT/requirements.txt" --quiet >&2
    "$VENV_PYTHON" -m playwright install chromium --quiet >&2
    echo "tabwright: venv ready." >&2
fi
export PYTHONPATH="$PLUGIN_ROOT"
exec "$VENV_PYTHON" -m tabwright.server
```

Make it executable: `chmod +x plugins/tabwright/run-server.sh`

- [ ] **Step 4: Write `install.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== tabwright installer ==="

echo "Setting up Python virtual environment..."
python3 -m venv "$SCRIPT_DIR/venv"
"$SCRIPT_DIR/venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" --quiet
echo "Python dependencies installed."

echo "Installing Playwright chromium browser..."
"$SCRIPT_DIR/venv/bin/python" -m playwright install chromium
echo "Playwright ready."

chmod +x "$SCRIPT_DIR/run-server.sh"

echo ""
echo "=== tabwright installed. ==="
echo "Run /plugin install to activate, then restart Claude Code."
```

Make it executable: `chmod +x plugins/tabwright/install.sh`

- [ ] **Step 5: Write `.mcp.json`**

```json
{
  "mcpServers": {
    "tabwright": {
      "command": "${CLAUDE_PLUGIN_ROOT}/run-server.sh",
      "args": [],
      "env": {}
    }
  }
}
```

- [ ] **Step 6: Write `.claude-plugin/plugin.json`**

```json
{
  "name": "tabwright",
  "version": "0.1.0",
  "description": "Human-like web crawler for Claude research via Playwright",
  "mcp": ".mcp.json"
}
```

- [ ] **Step 7: Commit**

```bash
cd /home/caleb/claude-plugins
git add plugins/tabwright/
git commit -m "feat(tabwright): scaffold plugin structure"
```

---

## Task 2: `stealth.py` — UA Rotation, Delay, Viewport

**Files:**
- Create: `plugins/tabwright/tabwright/stealth.py`
- Create: `plugins/tabwright/tests/test_stealth.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_stealth.py`:
```python
import asyncio
import pytest
from tabwright.stealth import random_user_agent, random_viewport, random_delay

USER_AGENT_KEYWORDS = ["Mozilla", "Chrome", "Firefox", "Safari"]

def test_random_user_agent_returns_string():
    ua = random_user_agent()
    assert isinstance(ua, str)
    assert any(kw in ua for kw in USER_AGENT_KEYWORDS)

def test_random_user_agent_varies():
    agents = {random_user_agent() for _ in range(20)}
    assert len(agents) > 1

def test_random_viewport_has_width_and_height():
    vp = random_viewport()
    assert "width" in vp and "height" in vp
    assert vp["width"] >= 1280
    assert vp["height"] >= 768

def test_random_viewport_varies():
    viewports = {(random_viewport()["width"], random_viewport()["height"]) for _ in range(20)}
    assert len(viewports) > 1

@pytest.mark.asyncio
async def test_random_delay_completes():
    await random_delay(min_s=0.01, max_s=0.05)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/caleb/claude-plugins/plugins/tabwright
python -m pytest tests/test_stealth.py -v 2>&1 | head -20
```

Expected: ImportError or ModuleNotFoundError for `tabwright.stealth`

- [ ] **Step 3: Write `tabwright/stealth.py`**

```python
import asyncio
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
]

VIEWPORTS = [
    {"width": 1280, "height": 800},
    {"width": 1440, "height": 900},
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
]


def random_user_agent() -> str:
    return random.choice(USER_AGENTS)


def random_viewport() -> dict:
    return random.choice(VIEWPORTS)


async def random_delay(min_s: float = 1.0, max_s: float = 3.0) -> None:
    await asyncio.sleep(random.uniform(min_s, max_s))
```

- [ ] **Step 4: Install deps and run tests**

```bash
cd /home/caleb/claude-plugins/plugins/tabwright
python3 -m venv venv
venv/bin/pip install -r requirements.txt --quiet
PYTHONPATH=. venv/bin/python -m pytest tests/test_stealth.py -v
```

Expected: 5 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/caleb/claude-plugins
git add plugins/tabwright/tabwright/stealth.py plugins/tabwright/tests/test_stealth.py
git commit -m "feat(tabwright): add stealth helpers (UA, delay, viewport)"
```

---

## Task 3: `browser.py` — Singleton Browser Lifecycle

**Files:**
- Create: `plugins/tabwright/tabwright/browser.py`

No unit test for this module — it requires a real Playwright browser and is covered by integration tests in Task 8.

- [ ] **Step 1: Write `tabwright/browser.py`**

```python
import os
from playwright.async_api import async_playwright, Browser, BrowserContext, Playwright

from tabwright.stealth import random_user_agent, random_viewport

_playwright: Playwright | None = None
_browser: Browser | None = None


async def _ensure_browser() -> Browser:
    global _playwright, _browser
    if _browser is not None and _browser.is_connected():
        return _browser
    headless = os.getenv("TABWRIGHT_HEADLESS", "false").lower() == "true"
    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch(headless=headless)
    return _browser


async def new_context() -> BrowserContext:
    browser = await _ensure_browser()
    return await browser.new_context(
        user_agent=random_user_agent(),
        viewport=random_viewport(),
    )


async def close_browser() -> None:
    global _browser, _playwright
    if _browser is not None:
        await _browser.close()
        _browser = None
    if _playwright is not None:
        await _playwright.stop()
        _playwright = None
```

- [ ] **Step 2: Verify import works**

```bash
cd /home/caleb/claude-plugins/plugins/tabwright
PYTHONPATH=. venv/bin/python -c "from tabwright.browser import new_context, close_browser; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
cd /home/caleb/claude-plugins
git add plugins/tabwright/tabwright/browser.py
git commit -m "feat(tabwright): add singleton Playwright browser manager"
```

---

## Task 4: `fetcher.py` — Generic HTML → Markdown

**Files:**
- Create: `plugins/tabwright/tabwright/fetcher.py`
- Create: `plugins/tabwright/tests/test_fetcher.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_fetcher.py`:
```python
from tabwright.fetcher import html_to_markdown

SAMPLE_HTML = """
<html>
<head><style>body { color: red; }</style></head>
<body>
  <nav>Skip nav</nav>
  <header>Skip header</header>
  <main>
    <h1>Main Title</h1>
    <p>This is the content paragraph.</p>
    <ul><li>Item one</li><li>Item two</li></ul>
  </main>
  <footer>Skip footer</footer>
  <script>alert('skip')</script>
</body>
</html>
"""

def test_extracts_main_content():
    md = html_to_markdown(SAMPLE_HTML)
    assert "Main Title" in md
    assert "content paragraph" in md

def test_strips_boilerplate():
    md = html_to_markdown(SAMPLE_HTML)
    assert "Skip nav" not in md
    assert "Skip header" not in md
    assert "Skip footer" not in md
    assert "alert" not in md

def test_converts_list_to_markdown():
    md = html_to_markdown(SAMPLE_HTML)
    assert "Item one" in md
    assert "Item two" in md

def test_empty_html_returns_empty_string():
    md = html_to_markdown("")
    assert isinstance(md, str)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/caleb/claude-plugins/plugins/tabwright
PYTHONPATH=. venv/bin/python -m pytest tests/test_fetcher.py -v 2>&1 | head -20
```

Expected: ImportError for `tabwright.fetcher`

- [ ] **Step 3: Write `tabwright/fetcher.py`**

```python
from bs4 import BeautifulSoup
from markdownify import markdownify

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
    except Exception as e:
        error = "timeout" if "timeout" in str(e).lower() else "blocked"
        return {"url": url, "content": "", "content_type": "generic", "error": error}
    finally:
        await context.close()
```

- [ ] **Step 4: Run tests**

```bash
cd /home/caleb/claude-plugins/plugins/tabwright
PYTHONPATH=. venv/bin/python -m pytest tests/test_fetcher.py -v
```

Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/caleb/claude-plugins
git add plugins/tabwright/tabwright/fetcher.py plugins/tabwright/tests/test_fetcher.py
git commit -m "feat(tabwright): add generic HTML-to-markdown fetcher"
```

---

## Task 5: `reddit.py` — Reddit Post + Comment Extractor

**Files:**
- Create: `plugins/tabwright/tabwright/reddit.py`
- Create: `plugins/tabwright/tests/fixtures/reddit_post.html`
- Create: `plugins/tabwright/tests/test_reddit.py`

- [ ] **Step 1: Create a minimal Reddit fixture HTML**

Save as `tests/fixtures/reddit_post.html`:
```html
<!DOCTYPE html>
<html>
<body>
  <h1>How do I reverse a list in Python?</h1>
  <shreddit-post score="1234" author="testuser">
    <div slot="text-body">You can use list.reverse() or reversed() or slicing [::-1].</div>
  </shreddit-post>
  <shreddit-comment author="commenter1" score="42">
    <div slot="comment">I prefer my_list[::-1] for a new list.</div>
  </shreddit-comment>
  <shreddit-comment author="commenter2" score="17">
    <div slot="comment">reversed() returns an iterator, useful for large lists.</div>
  </shreddit-comment>
</body>
</html>
```

- [ ] **Step 2: Write the failing tests**

`tests/test_reddit.py`:
```python
from pathlib import Path
from tabwright.reddit import extract_reddit

FIXTURE = (Path(__file__).parent / "fixtures" / "reddit_post.html").read_text()
URL = "https://www.reddit.com/r/learnpython/comments/abc123/how_do_i_reverse/"


def test_extracts_title():
    result = extract_reddit(FIXTURE, URL)
    assert "How do I reverse a list in Python?" in result["content"]


def test_extracts_post_body():
    result = extract_reddit(FIXTURE, URL)
    assert "list.reverse()" in result["content"]


def test_extracts_comments():
    result = extract_reddit(FIXTURE, URL)
    assert "commenter1" in result["content"]
    assert "my_list[::-1]" in result["content"]
    assert "commenter2" in result["content"]
    assert "iterator" in result["content"]


def test_includes_score_and_author():
    result = extract_reddit(FIXTURE, URL)
    assert "1234" in result["content"]
    assert "testuser" in result["content"]


def test_content_type_is_reddit():
    result = extract_reddit(FIXTURE, URL)
    assert result["content_type"] == "reddit"


def test_url_preserved():
    result = extract_reddit(FIXTURE, URL)
    assert result["url"] == URL
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd /home/caleb/claude-plugins/plugins/tabwright
PYTHONPATH=. venv/bin/python -m pytest tests/test_reddit.py -v 2>&1 | head -20
```

Expected: ImportError for `tabwright.reddit`

- [ ] **Step 4: Write `tabwright/reddit.py`**

```python
from bs4 import BeautifulSoup


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
```

- [ ] **Step 5: Run tests**

```bash
cd /home/caleb/claude-plugins/plugins/tabwright
PYTHONPATH=. venv/bin/python -m pytest tests/test_reddit.py -v
```

Expected: 6 tests PASS

- [ ] **Step 6: Commit**

```bash
cd /home/caleb/claude-plugins
git add plugins/tabwright/tabwright/reddit.py plugins/tabwright/tests/test_reddit.py plugins/tabwright/tests/fixtures/reddit_post.html
git commit -m "feat(tabwright): add Reddit post+comment extractor"
```

---

## Task 6: `search.py` — DuckDuckGo Search + Reddit Reranking

**Files:**
- Create: `plugins/tabwright/tabwright/search.py`

No unit test — requires a real browser. Covered by integration tests in Task 8.

- [ ] **Step 1: Write `tabwright/search.py`**

```python
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
        await context.close()
```

- [ ] **Step 2: Verify import works**

```bash
cd /home/caleb/claude-plugins/plugins/tabwright
PYTHONPATH=. venv/bin/python -c "from tabwright.search import web_search; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
cd /home/caleb/claude-plugins
git add plugins/tabwright/tabwright/search.py
git commit -m "feat(tabwright): add DuckDuckGo search with Reddit reranking"
```

---

## Task 7: `server.py` — FastMCP Tool Registration

**Files:**
- Create: `plugins/tabwright/tabwright/server.py`

- [ ] **Step 1: Write `tabwright/server.py`**

```python
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

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
        except Exception as e:
            error = "timeout" if "timeout" in str(e).lower() else "blocked"
            return {"url": url, "content": "", "content_type": "reddit", "error": error}
        finally:
            await context.close()
    return await _fetch_generic(url)


if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 2: Verify the server starts without error**

```bash
cd /home/caleb/claude-plugins/plugins/tabwright
PYTHONPATH=. timeout 3 venv/bin/python -m tabwright.server 2>&1 || true
```

Expected: No import errors (timeout is expected since the server waits for MCP input)

- [ ] **Step 3: Commit**

```bash
cd /home/caleb/claude-plugins
git add plugins/tabwright/tabwright/server.py
git commit -m "feat(tabwright): wire FastMCP server with web_search and fetch_page tools"
```

---

## Task 8: Integration Tests

**Files:**
- Create: `plugins/tabwright/tests/test_integration.py`

These tests launch a real browser. They are skipped automatically when `TABWRIGHT_HEADLESS` is not set and no display is available, or can be forced headless with `TABWRIGHT_HEADLESS=true`.

- [ ] **Step 1: Write `tests/test_integration.py`**

```python
import os
import pytest
import pytest_asyncio

# Skip all tests in this module if TABWRIGHT_SKIP_INTEGRATION is set
pytestmark = pytest.mark.skipif(
    os.getenv("TABWRIGHT_SKIP_INTEGRATION", "false").lower() == "true",
    reason="Integration tests skipped (TABWRIGHT_SKIP_INTEGRATION=true)",
)


@pytest.fixture(autouse=True)
def set_headless(monkeypatch):
    monkeypatch.setenv("TABWRIGHT_HEADLESS", "true")


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
        # Use a non-routable IP to force timeout
        result = await fetch_page("http://192.0.2.1/")
        assert "error" in result
        assert result["error"] in ("timeout", "blocked")
    finally:
        await close_browser()
```

- [ ] **Step 2: Run unit tests to confirm nothing is broken**

```bash
cd /home/caleb/claude-plugins/plugins/tabwright
PYTHONPATH=. venv/bin/python -m pytest tests/test_stealth.py tests/test_fetcher.py tests/test_reddit.py -v
```

Expected: All unit tests PASS

- [ ] **Step 3: Run integration tests (headless)**

```bash
cd /home/caleb/claude-plugins/plugins/tabwright
TABWRIGHT_HEADLESS=true PYTHONPATH=. venv/bin/python -m pytest tests/test_integration.py -v --timeout=60
```

Expected: All integration tests PASS (may be slow on first run due to browser launch)

- [ ] **Step 4: Commit**

```bash
cd /home/caleb/claude-plugins
git add plugins/tabwright/tests/test_integration.py
git commit -m "feat(tabwright): add integration tests for search and fetch tools"
```

---

## Task 9: Final Wiring + README

**Files:**
- Create: `plugins/tabwright/README.md`

- [ ] **Step 1: Write `README.md`**

```markdown
# tabwright

MCP plugin for Claude Code — gives Claude a human-like Playwright browser for web research.

## Tools

### `web_search(query, prefer_reddit=False, max_results=10)`
Searches DuckDuckGo and returns `[{title, url, snippet}, ...]`. Use `prefer_reddit=True` to float Reddit results to the top.

### `fetch_page(url)`
Fetches a page and returns `{url, content, content_type}` where content is clean markdown. Automatically uses Reddit-optimised extraction for `reddit.com` URLs.

## Install

```bash
cd plugins/tabwright
./install.sh
```

Then run `/plugin install` in Claude Code and restart.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `TABWRIGHT_HEADLESS` | `false` | Set to `true` for headless mode (CI/servers) |
| `TABWRIGHT_SKIP_INTEGRATION` | `false` | Set to `true` to skip integration tests |

## Running Tests

```bash
# Unit tests only
PYTHONPATH=. venv/bin/python -m pytest tests/test_stealth.py tests/test_fetcher.py tests/test_reddit.py -v

# All tests including integration (headless)
TABWRIGHT_HEADLESS=true PYTHONPATH=. venv/bin/python -m pytest tests/ -v
```
```

- [ ] **Step 2: Run the full test suite one final time**

```bash
cd /home/caleb/claude-plugins/plugins/tabwright
TABWRIGHT_HEADLESS=true PYTHONPATH=. venv/bin/python -m pytest tests/ -v
```

Expected: All tests PASS

- [ ] **Step 3: Final commit**

```bash
cd /home/caleb/claude-plugins
git add plugins/tabwright/README.md
git commit -m "feat(tabwright): add README and complete plugin"
```
