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
