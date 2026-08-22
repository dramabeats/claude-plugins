# tabwright

MCP plugin for Claude Code — gives Claude a human-like Playwright browser for web research.

## Tools

### `web_search(query, prefer_reddit=False, max_results=10)`
Searches DuckDuckGo and returns `[{title, url, snippet}, ...]`. Use `prefer_reddit=True` to float Reddit results to the top.

### `fetch_page(url)`
Fetches a page and returns `{url, content, content_type}` where content is clean markdown. Automatically uses Reddit-optimised extraction for `reddit.com` URLs.

## Tabs

`web_search` and `fetch_page` are one-shot: each opens a throwaway context. Tabs are for multi-step work — filling a form, following a flow, reading a page that only renders after interaction. A tab persists across tool calls until you close it.

### `open_tab(name)` / `close_tab(name)` / `list_tabs()`
Named tabs, each in its own browser context. `open_tab` errors if the name is taken.

### `navigate(name, url)`
Returns `{name, url, title}`.

### `snapshot(name)`
Returns `{name, url, snapshot}` — an ARIA tree of the page. Read the accessible names out of this and pass them to `click` / `type_text`.

### `click(name, ref)` / `type_text(name, ref, text)`
`ref` is an accessible name as shown in `snapshot()`. It is resolved against, in order: `aria-label`, placeholder, ARIA role + name, `title`, and visible text — exact matches before fuzzy — falling back to treating `ref` as a raw CSS/XPath selector. Where several nodes match, the first visible one wins, so an ambiguous name is never an error.

If nothing matches, both return `{error}` immediately rather than blocking until timeout.

```
navigate("s", "https://en.wikipedia.org")
snapshot("s")                                   # find the accessible names
type_text("s", "Search Wikipedia", "Doha Agreement")
click("s", "Search")
close_tab("s")
```

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
PYTHONPATH=. venv/bin/python -m pytest tests/test_stealth.py tests/test_fetcher.py tests/test_reddit.py tests/test_tabs.py -v

# All tests including integration (headless)
TABWRIGHT_HEADLESS=true PYTHONPATH=. venv/bin/python -m pytest tests/ -v
```
