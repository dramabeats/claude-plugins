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
