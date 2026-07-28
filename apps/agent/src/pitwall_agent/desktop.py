"""Native desktop window.

Double-clicking the executable has to open a window with numbers in it. The
hub still runs, because that is what the strategist connects to over the
tailnet, but the driver never has to see a browser or a URL.

The window hosts the same UI through Edge WebView2, which ships with Windows
11. That keeps one implementation of the readouts instead of two.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass

import uvicorn
import webview
from pitwall_hub.app import app, mount_web_ui, registry

from pitwall_agent.serve import ServeConfig, stream_forever
from pitwall_agent.tailnet import detect as detect_tailnet
from pitwall_agent.web_assets import find_web_build

WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 720


@dataclass(frozen=True)
class DesktopStartup:
    """What the window needs to know before it opens."""

    url: str
    title: str


def _startup(config: ServeConfig) -> DesktopStartup:
    identity = detect_tailnet()
    reachable = identity.dns_name or identity.ip if identity else config.host

    # Prefill the form so the driver's own car needs no typing. A blank host
    # means "the machine serving this page", which is this one.
    query = f"?host=&room={config.room_code}"
    if config.token:
        query += f"&token={config.token}"

    # The window must load the address the server actually bound. Pointing it
    # at 127.0.0.1 while uvicorn listens on the tailnet address gives a window
    # that cannot reach its own hub.
    return DesktopStartup(
        url=f"http://{config.host}:{config.port}/{query}",
        title=f"PitWall — {config.room_code} — {reachable}:{config.port}",
    )


def run(config: ServeConfig) -> int:
    build = find_web_build()
    if build is None or not mount_web_ui(build):
        # Without the UI there is no window to show, and silently opening a
        # blank one would be worse than saying so.
        webview.create_window(
            "PitWall",
            html=(
                "<body style='background:#0a0a0a;color:#e5e5e5;font:14px sans-serif;padding:32px'>"
                "<h2>Интерфейс не собран</h2>"
                "<p>Сборка веб-интерфейса не найдена в пакете.</p>"
                "<p><code>npm run build --workspace @pitwall/web</code></p>"
                "</body>"
            ),
            width=560,
            height=280,
        )
        webview.start()
        return 1

    room = registry.create(token=config.token, code=config.room_code)
    room.rate_hz = config.rate_hz

    server = uvicorn.Server(
        uvicorn.Config(app, host=config.host, port=config.port, log_level="warning")
    )

    # Both the server and the telemetry loop are daemons: closing the window is
    # how the driver quits, and it must not leave a process behind.
    threading.Thread(target=server.run, daemon=True).start()
    threading.Thread(target=stream_forever, args=(room, config), daemon=True).start()

    startup = _startup(config)
    webview.create_window(
        startup.title,
        startup.url,
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        background_color="#0a0a0a",
    )
    webview.start()
    return 0
