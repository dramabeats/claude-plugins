# Tabwright — Design Spec

**Date:** 2026-05-19  
**Status:** Approved

## Overview

Tabwright is a Claude Code MCP plugin that gives Claude a human-like web browser for research. It exposes two tools — `web_search` and `fetch_page` — that Claude calls autonomously when asked to research a topic or problem. The Playwright browser applies basic stealth techniques to avoid bot detection. Reddit is the primary target but the tool works on any public site.

## Goals

- Let Claude search the web and read pages as part of a prompt workflow
- Return clean markdown suitable for direct use in LLM prompts
- Handle Reddit's JS-rendered content reliably
- Avoid bot detection without heavy infrastructure (no proxies in v1)

## Architecture

Two FastMCP tools served from a Python MCP server. A singleton Playwright browser is lazily initialized on first call and reused across calls to avoid startup overhead.

```
plugins/tabwright/
├── .claude-plugin/plugin.json
├── .mcp.json
├── tabwright/
│   ├── __init__.py
│   ├── server.py       # FastMCP entry point
│   ├── browser.py      # Singleton browser lifecycle
│   ├── search.py       # DuckDuckGo scraping + Reddit reranking
│   ├── fetcher.py      # Generic HTML → markdown
│   ├── reddit.py       # Reddit-specific extractor
│   └── stealth.py      # User-agent rotation, delays, viewport
├── tests/
│   ├── test_search.py
│   └── test_fetch.py
├── pyproject.toml
└── run-server.sh
```

## Tools

### `web_search`

```
web_search(query: str, prefer_reddit: bool = False, max_results: int = 10)
→ list[{title: str, url: str, snippet: str}]
```

1. Acquire browser singleton
2. Navigate to DuckDuckGo with the query
3. Apply a random 1–3s delay before interacting
4. Scrape up to `max_results` result cards (title, URL, snippet)
5. If `prefer_reddit=True`: sort Reddit URLs to the top, keep others after
6. Return the list

### `fetch_page`

```
fetch_page(url: str)
→ {url: str, content: str, content_type: "reddit" | "generic", error?: str}
```

1. Detect Reddit URL (`reddit.com` in host)
2. **Reddit path:** navigate with Playwright, wait for post content to render, extract via `reddit.py` into structured markdown:
   ```
   # Post Title
   **Score:** 1234 | **Author:** username
   
   Post body text...
   
   ## Comments
   **username** (score: 42)
   Comment text...
   ```
3. **Generic path:** navigate, wait for `networkidle`, convert HTML to markdown via `markdownify`, strip boilerplate (`nav`, `header`, `footer`, `aside`, `script`, `style`)
4. Return content with `content_type` tag

## Stealth

Applied in `stealth.py`, used by both tools:

- User-agent rotated from a curated list of recent Chrome/Firefox UAs
- Random delay 1–3s between navigation actions
- Viewport randomized within common desktop resolutions (1280–1920 wide)
- Browser launched non-headless by default (visible window is hardest to detect)
- `--headless` flag available for CI/server environments

No proxy rotation in v1. If a page returns an error or times out, the tool returns `{error: "blocked"|"timeout", url}` and Claude moves on to the next result.

## Error Handling

| Scenario | Behaviour |
|---|---|
| Page timeout (30s) | Return `{error: "timeout", url}` |
| Navigation blocked / CAPTCHA | Return `{error: "blocked", url}` |
| Browser crash | Reinitialize singleton on next call |
| DuckDuckGo layout change | `web_search` raises a descriptive exception |

## Dependencies

- `playwright` — browser automation
- `fastmcp` — MCP server framework
- `markdownify` — HTML to markdown
- `beautifulsoup4` — HTML parsing for Reddit extractor

## Testing

Integration tests using real URLs, skipped automatically if no display is available (`DISPLAY` not set and `--headless` not passed). One test per tool covering the happy path and the Reddit-specific extractor.

## Plugin Manifest

Follows the same `plugin.json` / `.mcp.json` pattern as other plugins in this repo. Server entry point: `run-server.sh` invoking `python -m tabwright.server`.

## Out of Scope (v1)

- Proxy rotation
- Login / authenticated sessions
- Pagination / recursive crawling beyond a single page
- Rate limiting / request queuing
