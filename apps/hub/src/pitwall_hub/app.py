"""Hub HTTP surface.

Rooms, fan-out and session history land in M6. What exists now is the health
endpoint, because the release smoke test starts the executable and waits for it.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pitwall_schema import CHANNELS, PROTOCOL_VERSION

app = FastAPI(title="PitWall Hub", version="0.0.1")


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "protocol_version": PROTOCOL_VERSION,
        "channel_count": len(CHANNELS),
    }
