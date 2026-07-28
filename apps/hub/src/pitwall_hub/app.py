"""Hub HTTP and WebSocket surface.

The driver's machine runs this. The strategist reaches it over Tailscale, so
there is no public exposure and no TLS termination to arrange here — the tailnet
authenticates the device and the room code authorises the session.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import msgpack
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pitwall_schema import CHANNELS, PROTOCOL_VERSION

from pitwall_hub.rooms import Room, RoomRegistry

# Populated by the launcher so the agent can publish without a network hop.
registry = RoomRegistry()

app = FastAPI(title="PitWall Hub", version="0.0.1")


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "protocol_version": PROTOCOL_VERSION,
        "channel_count": len(CHANNELS),
        "rooms": [room.describe() for room in registry.all()],
    }


def _encode(frame_id: str, payload: dict[str, Any]) -> bytes:
    return bytes(msgpack.packb({"f": frame_id, **payload}, use_bin_type=True))


async def _reject(websocket: WebSocket, code: str, message: str) -> None:
    await websocket.send_bytes(_encode("error", {"code": code, "message": message}))
    await websocket.close()


@app.websocket("/ws/view")
async def websocket_view(websocket: WebSocket, room: str = "", token: str = "") -> None:
    """A strategist or engineer subscribing to a room."""
    await websocket.accept()

    target: Room | None = registry.get(room)
    if target is None:
        await _reject(websocket, "no_such_room", f"Room {room!r} does not exist")
        return

    if not target.authorises(token or None):
        await _reject(websocket, "unauthorised", "Wrong or missing room token")
        return

    await websocket.send_bytes(
        _encode(
            "welcome",
            {
                "session_id": target.code,
                "channels": target.channels,
                "rate_hz": target.rate_hz,
                "game": target.status.game,
            },
        )
    )
    await websocket.send_bytes(
        _encode(
            "agent_status",
            {
                "connected_to_game": target.status.connected_to_game,
                "game": target.status.game,
                "problem": target.status.problem,
            },
        )
    )

    await target.add_viewer(websocket)
    try:
        while True:
            # Viewers do not push telemetry; this keeps the socket alive and
            # notices a disconnect.
            await websocket.receive_bytes()
    except WebSocketDisconnect:
        pass
    finally:
        await target.remove_viewer(websocket)


def mount_web_ui(directory: Path) -> bool:
    """Serve the built front end, if it was bundled.

    Returns False when the build is absent so the launcher can say so instead
    of leaving the strategist with a blank page and no explanation.
    """
    index = directory / "index.html"
    if not index.is_file():
        return False

    app.mount("/assets", StaticFiles(directory=directory / "assets"), name="assets")

    @app.get("/")
    def serve_index() -> FileResponse:
        return FileResponse(index)

    return True
