"""Fan-out behaviour.

The rule that matters: one viewer failing must not cost the others their data.
A strategist on hotel wifi cannot be allowed to stall the driver's stream.
"""

from __future__ import annotations

import pytest
from pitwall_hub.rooms import ROOM_ALPHABET, Room, generate_room_code, is_valid_room_code


class RecordingSender:
    def __init__(self) -> None:
        self.received: list[bytes] = []

    async def send_bytes(self, data: bytes) -> None:
        self.received.append(data)


class BrokenSender:
    async def send_bytes(self, data: bytes) -> None:
        raise ConnectionResetError("viewer went away")


async def test_broadcast_reaches_every_viewer() -> None:
    room = Room(code="BCDFGH")
    first, second = RecordingSender(), RecordingSender()
    await room.add_viewer(first)
    await room.add_viewer(second)

    await room.broadcast(b"payload")

    assert first.received == [b"payload"]
    assert second.received == [b"payload"]


async def test_a_failing_viewer_is_dropped_without_affecting_the_others() -> None:
    room = Room(code="BCDFGH")
    good = RecordingSender()
    await room.add_viewer(BrokenSender())
    await room.add_viewer(good)

    await room.broadcast(b"payload")

    assert good.received == [b"payload"]
    assert room.viewers == {good}


async def test_broadcast_survives_every_viewer_failing() -> None:
    room = Room(code="BCDFGH")
    await room.add_viewer(BrokenSender())

    await room.broadcast(b"payload")

    assert room.viewers == set()


def test_a_room_without_a_token_admits_anyone() -> None:
    assert Room(code="BCDFGH").authorises(None)


def test_a_token_room_rejects_a_missing_token() -> None:
    room = Room(code="BCDFGH", token="secret")
    assert not room.authorises(None)
    assert not room.authorises("")
    assert room.authorises("secret")


def test_generated_codes_avoid_ambiguous_characters() -> None:
    """Codes get read out over voice comms mid-race."""
    for _ in range(200):
        code = generate_room_code()
        assert len(code) == 6
        assert set(code) <= set(ROOM_ALPHABET)
        assert not set(code) & set("AEIOU01")


@pytest.mark.parametrize("code", ["BCDFGH", "bcdfgh", "234567"])
def test_valid_codes_are_accepted_case_insensitively(code: str) -> None:
    assert is_valid_room_code(code)


@pytest.mark.parametrize("code", ["BCDFG", "BCDFGHJ", "BCDFGA", "BCDF-H", ""])
def test_invalid_codes_are_rejected(code: str) -> None:
    assert not is_valid_room_code(code)
