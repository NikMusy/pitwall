"""Room registry and fan-out.

One room holds at most one live telemetry source and any number of viewers.
Viewers are independent: a strategist on a slow link must not be able to stall
the stream for anyone else, so a send that fails drops that viewer rather than
blocking the loop.
"""

from __future__ import annotations

import asyncio
import secrets
from dataclasses import dataclass, field
from typing import Any, Protocol

ROOM_CODE_LENGTH = 6
# No vowels, so a generated code cannot spell something and cannot be misread
# over voice comms mid-race.
ROOM_ALPHABET = "BCDFGHJKLMNPQRSTVWXZ23456789"


def generate_room_code() -> str:
    return "".join(secrets.choice(ROOM_ALPHABET) for _ in range(ROOM_CODE_LENGTH))


def is_valid_room_code(code: str) -> bool:
    return len(code) == ROOM_CODE_LENGTH and all(c in ROOM_ALPHABET for c in code.upper())


class Sender(Protocol):
    async def send_bytes(self, data: bytes) -> None: ...


@dataclass
class AgentStatus:
    """What the driver's machine can currently see.

    `problem` is shown to the strategist verbatim. A disconnected agent is a
    fact the pit wall needs, not something to paper over.
    """

    connected_to_game: bool = False
    game: str | None = None
    problem: str | None = None


@dataclass
class Room:
    code: str
    token: str | None = None
    channels: list[str] = field(default_factory=list)
    rate_hz: int = 0
    status: AgentStatus = field(default_factory=AgentStatus)
    viewers: set[Sender] = field(default_factory=set)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def authorises(self, token: str | None) -> bool:
        if self.token is None:
            return True
        return secrets.compare_digest(self.token, token or "")

    async def broadcast(self, payload: bytes) -> None:
        """Send to every viewer, dropping the ones that fail."""
        async with self._lock:
            targets = list(self.viewers)

        dead: list[Sender] = []
        for viewer in targets:
            try:
                await viewer.send_bytes(payload)
            except Exception:
                dead.append(viewer)

        if dead:
            async with self._lock:
                self.viewers.difference_update(dead)

    async def add_viewer(self, viewer: Sender) -> None:
        async with self._lock:
            self.viewers.add(viewer)

    async def remove_viewer(self, viewer: Sender) -> None:
        async with self._lock:
            self.viewers.discard(viewer)

    def describe(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "channels": self.channels,
            "rate_hz": self.rate_hz,
            "viewers": len(self.viewers),
            "connected_to_game": self.status.connected_to_game,
            "game": self.status.game,
            "problem": self.status.problem,
        }


class RoomRegistry:
    def __init__(self) -> None:
        self._rooms: dict[str, Room] = {}

    def create(self, token: str | None = None, code: str | None = None) -> Room:
        code = (code or generate_room_code()).upper()
        room = Room(code=code, token=token)
        self._rooms[code] = room
        return room

    def get(self, code: str) -> Room | None:
        return self._rooms.get(code.upper())

    def all(self) -> list[Room]:
        return list(self._rooms.values())
