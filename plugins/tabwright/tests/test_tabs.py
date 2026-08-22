import pytest
from unittest.mock import AsyncMock, patch

from tabwright import tabs as tabs_mod


def _mock_page_with(match_on: str, url: str = "https://example.com"):
    """Mock page whose only resolvable strategy is `match_on`.

    Every other get_by_* strategy reports zero matches, so each test also
    proves the resolver falls through to the strategy it names.
    """
    node = AsyncMock()
    node.is_visible = AsyncMock(return_value=True)

    hit = AsyncMock()
    hit.count = AsyncMock(return_value=1)
    hit.nth = lambda i: node
    hit.first = node

    miss = AsyncMock()
    miss.count = AsyncMock(return_value=0)

    page = AsyncMock()
    page.url = url
    page.wait_for_load_state = AsyncMock()
    page.wait_for_timeout = AsyncMock()
    for strategy in ("get_by_label", "get_by_placeholder", "get_by_role",
                     "get_by_title", "get_by_text", "locator"):
        setattr(
            page,
            strategy,
            (lambda s: lambda *a, **k: hit if s == match_on else miss)(strategy),
        )
    return page, node


def _with_tab(page):
    return patch.object(tabs_mod.tabs, "get", new_callable=AsyncMock, return_value=page)


# ── click ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_click_by_aria_label():
    page, node = _mock_page_with("get_by_label")
    with _with_tab(page):
        assert await tabs_mod.click("t", "Submit") == {
            "name": "t", "url": "https://example.com"}
        node.click.assert_called_once()


@pytest.mark.asyncio
async def test_click_falls_back_to_link_text():
    """An <a>Learn more</a> with no aria-label must still be clickable."""
    page, node = _mock_page_with("get_by_role")
    with _with_tab(page):
        assert "error" not in await tabs_mod.click("t", "Learn more")
        node.click.assert_called_once()


@pytest.mark.asyncio
async def test_click_falls_back_to_css_selector():
    page, node = _mock_page_with("locator")
    with _with_tab(page):
        assert "error" not in await tabs_mod.click("t", "a[href]")
        node.click.assert_called_once()


@pytest.mark.asyncio
async def test_click_picks_first_visible_when_ref_is_ambiguous():
    """Two nodes share a label; strict mode must not be triggered."""
    hidden, visible = AsyncMock(), AsyncMock()
    hidden.is_visible = AsyncMock(return_value=False)
    visible.is_visible = AsyncMock(return_value=True)

    loc = AsyncMock()
    loc.count = AsyncMock(return_value=2)
    loc.nth = lambda i: (hidden, visible)[i]

    page, _ = _mock_page_with("nothing-matches")
    page.get_by_label = lambda *a, **k: loc

    with _with_tab(page):
        assert "error" not in await tabs_mod.click("t", "Search Wikipedia")
    visible.click.assert_called_once()
    hidden.click.assert_not_called()


@pytest.mark.asyncio
async def test_click_no_match_returns_error():
    page, _ = _mock_page_with("nothing-matches")
    with _with_tab(page):
        result = await tabs_mod.click("t", "zzz")
    assert "error" in result and "zzz" in result["error"]


@pytest.mark.asyncio
async def test_click_missing_tab_returns_error():
    with patch.object(tabs_mod.tabs, "get", new_callable=AsyncMock) as get:
        get.side_effect = ValueError("Tab 'x' not found")
        assert "error" in await tabs_mod.click("x", "Submit")


# ── type_text ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_type_text_by_aria_label():
    page, node = _mock_page_with("get_by_label")
    with _with_tab(page):
        assert await tabs_mod.type_text("t", "Search box", "asyncio") == {
            "name": "t", "url": "https://example.com"}
        node.fill.assert_called_once_with("asyncio", timeout=15000)


@pytest.mark.asyncio
async def test_type_text_falls_back_to_placeholder():
    page, node = _mock_page_with("get_by_placeholder")
    with _with_tab(page):
        assert "error" not in await tabs_mod.type_text("t", "Search", "doha")
        node.fill.assert_called_once()


@pytest.mark.asyncio
async def test_type_text_no_match_returns_error():
    page, _ = _mock_page_with("nothing-matches")
    with _with_tab(page):
        assert "error" in await tabs_mod.type_text("t", "zzz", "x")


# ── tab lifecycle ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_open_tab_rejects_duplicate_name():
    with patch.object(tabs_mod.tabs, "open", new_callable=AsyncMock) as op:
        op.side_effect = ValueError("Tab 'x' already exists")
        assert "error" in await tabs_mod.open_tab("x")


@pytest.mark.asyncio
async def test_list_tabs():
    with patch.object(tabs_mod.tabs, "list", return_value={"a": "https://x"}):
        assert await tabs_mod.list_tabs() == {"tabs": {"a": "https://x"}}
