"""Startup wiring for the desktop window."""

from __future__ import annotations

from pitwall_agent.desktop import _startup
from pitwall_agent.serve import ServeConfig

CONFIG = ServeConfig(host="100.78.142.74", port=8420, room_code="BCDFGH", token=None, rate_hz=50)


def test_window_loads_the_address_the_server_bound() -> None:
    """A window pointed at 127.0.0.1 while uvicorn listens on the tailnet
    address cannot reach its own hub — it looks like the app is broken."""
    assert _startup(CONFIG).url.startswith("http://100.78.142.74:8420/")


def test_the_drivers_own_room_is_prefilled() -> None:
    url = _startup(CONFIG).url
    # Blank host means "the machine serving this page", so the driver sees
    # their own car without typing anything.
    assert "host=&" in url
    assert "room=BCDFGH" in url


def test_no_token_in_the_url_when_none_is_set() -> None:
    assert "token" not in _startup(CONFIG).url


def test_token_is_passed_through_when_set() -> None:
    config = ServeConfig(host="127.0.0.1", port=1, room_code="BCDFGH", token="secret", rate_hz=50)
    assert "token=secret" in _startup(config).url


def test_title_carries_the_room_code() -> None:
    """The driver reads the code off the title bar to give to the strategist."""
    assert "BCDFGH" in _startup(CONFIG).title
