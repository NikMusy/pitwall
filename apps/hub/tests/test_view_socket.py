"""The strategist's connection path."""

from __future__ import annotations

import msgpack
from fastapi.testclient import TestClient
from pitwall_hub.app import app, registry

client = TestClient(app)


def _decode(payload: bytes) -> dict[str, object]:
    decoded = msgpack.unpackb(payload, raw=False)
    assert isinstance(decoded, dict)
    return decoded


def test_unknown_room_is_refused_with_a_reason() -> None:
    with client.websocket_connect("/ws/view?room=ZZZZZZ") as socket:
        frame = _decode(socket.receive_bytes())

    assert frame["f"] == "error"
    assert frame["code"] == "no_such_room"


def test_wrong_token_is_refused() -> None:
    registry.create(token="correct-horse", code="BCDFGH")

    with client.websocket_connect("/ws/view?room=BCDFGH&token=wrong") as socket:
        frame = _decode(socket.receive_bytes())

    assert frame["f"] == "error"
    assert frame["code"] == "unauthorised"


def test_viewer_receives_welcome_then_agent_status() -> None:
    room = registry.create(code="JKLMNP")
    room.channels = ["speed", "throttle"]
    room.rate_hz = 50
    room.status.connected_to_game = False
    room.status.problem = "LMU is not running"

    with client.websocket_connect("/ws/view?room=JKLMNP") as socket:
        welcome = _decode(socket.receive_bytes())
        status = _decode(socket.receive_bytes())

    assert welcome["f"] == "welcome"
    assert welcome["channels"] == ["speed", "throttle"]

    # The strategist is told why there is nothing, rather than shown a blank
    # chart with no explanation.
    assert status["f"] == "agent_status"
    assert status["connected_to_game"] is False
    assert status["problem"] == "LMU is not running"


def test_viewer_is_registered_and_released() -> None:
    room = registry.create(code="QRSTVW")

    with client.websocket_connect("/ws/view?room=QRSTVW") as socket:
        socket.receive_bytes()  # welcome
        socket.receive_bytes()  # agent_status
        assert len(room.viewers) == 1

    assert room.viewers == set()
