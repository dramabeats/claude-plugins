"""Named tabs and element interaction.

Element resolution note: callers pass a `ref` they read out of snapshot(),
which reports *accessible names*. Those come from aria-label sometimes, but
far more often from link/button text, placeholder, or title. Resolving with
get_by_label() alone therefore misses most elements, and any label matching
more than one node trips Playwright's strict mode. Hence the cascade below,
which always narrows to a single node before acting.
"""

import logging

from tabwright.browser import tabs

logger = logging.getLogger(__name__)

_CLICK_ROLES = (
    "button", "link", "menuitem", "menuitemcheckbox", "menuitemradio",
    "tab", "option", "checkbox", "radio", "switch", "treeitem", "combobox",
)
_EDIT_ROLES = ("textbox", "combobox", "searchbox", "spinbutton")

_ACT_TIMEOUT = 15000


def _candidates(page, ref: str, editable: bool) -> list:
    """Locator strategies for `ref`, best-first. Exact matches before fuzzy."""
    roles = _EDIT_ROLES if editable else _CLICK_ROLES
    out = []
    for exact in (True, False):
        out.append(page.get_by_label(ref, exact=exact))
        out.append(page.get_by_placeholder(ref, exact=exact))
        for role in roles:
            out.append(page.get_by_role(role, name=ref, exact=exact))
        out.append(page.get_by_title(ref, exact=exact))
        if not editable:
            out.append(page.get_by_text(ref, exact=exact))
    # Last resort: treat `ref` as a raw CSS/XPath selector. Invalid or
    # non-matching selectors just yield no candidates, so this is safe to
    # try unconditionally rather than guessing at the syntax.
    out.append(page.locator(ref))
    return out


async def _pick(loc):
    """First visible node in `loc`, else its first node, else None."""
    try:
        n = await loc.count()
    except Exception:
        return None
    if n == 0:
        return None
    for i in range(min(n, 10)):
        node = loc.nth(i)
        try:
            if await node.is_visible():
                return node
        except Exception:
            continue
    return loc.first


async def _resolve(page, ref: str, editable: bool = False, tries: int = 3):
    """Find one actionable node for `ref`, retrying while the page settles."""
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=5000)
    except Exception:
        pass
    for attempt in range(tries):
        for loc in _candidates(page, ref, editable):
            node = await _pick(loc)
            if node is not None:
                return node
        if attempt < tries - 1:
            await page.wait_for_timeout(500)
    return None


def _no_match(name: str, ref: str, editable: bool) -> dict:
    what = "editable element" if editable else "element"
    return {
        "error": (
            f"No {what} found for ref {ref!r}. Take a snapshot and use an "
            f"accessible name exactly as it appears there, or pass a "
            f"CSS/XPath selector."
        ),
        "name": name,
    }


async def open_tab(name: str) -> dict:
    try:
        await tabs.open(name)
        return {"name": name, "opened": True}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e), "name": name}


async def navigate(name: str, url: str) -> dict:
    try:
        page = await tabs.get(name)
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        return {"name": name, "url": page.url, "title": await page.title()}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e), "name": name, "url": url}


async def snapshot(name: str) -> dict:
    try:
        page = await tabs.get(name)
        return {"name": name, "url": page.url, "snapshot": await page.aria_snapshot()}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e), "name": name}


async def click(name: str, ref: str) -> dict:
    try:
        page = await tabs.get(name)
        node = await _resolve(page, ref, editable=False)
        if node is None:
            return _no_match(name, ref, editable=False)
        await node.click(timeout=_ACT_TIMEOUT)
        # A click may navigate; settle so the returned url isn't stale.
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=10000)
        except Exception:
            pass
        return {"name": name, "url": page.url}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e), "name": name}


async def type_text(name: str, ref: str, text: str) -> dict:
    try:
        page = await tabs.get(name)
        node = await _resolve(page, ref, editable=True)
        if node is None:
            return _no_match(name, ref, editable=True)
        await node.fill(text, timeout=_ACT_TIMEOUT)
        return {"name": name, "url": page.url}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e), "name": name}


async def close_tab(name: str) -> dict:
    try:
        await tabs.close(name)
        return {"name": name, "closed": True}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e), "name": name}


async def list_tabs() -> dict:
    return {"tabs": tabs.list()}
