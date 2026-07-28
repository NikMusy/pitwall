"""Run the hub with a local telemetry source attached.

This is what the driver starts. The agent publishes into the room registry in
process — no network hop for the local car — and the strategist connects to the
same hub over Tailscale.

The loop keeps running when the game is absent. Losing LMU is a normal event
mid-session, and the strategist needs to see that it happened rather than watch
a frozen chart.
"""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
from pathlib import Path

import msgpack
import uvicorn
from pitwall_hub.app import app, mount_web_ui, registry
from pitwall_hub.rooms import Room

from pitwall_agent.ld.api import router as ld_router
from pitwall_agent.ld.source import GAME_ID as REPLAY_GAME_ID
from pitwall_agent.ld.source import LdReplaySource
from pitwall_agent.provider import ProviderUnavailableError
from pitwall_agent.rf2.provider import GAME_ID, LmuProvider
from pitwall_agent.rf2.reader import TornReadError
from pitwall_agent.web_assets import find_web_build

RETRY_INTERVAL_S = 3.0
BATCH_INTERVAL_S = 0.1


@dataclass(frozen=True)
class ServeConfig:
    host: str
    port: int
    room_code: str
    token: str | None
    rate_hz: int
    # Set to play a recorded .ld instead of reading live shared memory. The
    # frames are real recorded laps, and the UI labels the source so nobody
    # mistakes a replay for a live car.
    replay: Path | None = None


def _encode(frame_id: str, payload: dict[str, object]) -> bytes:
    return bytes(msgpack.packb({"f": frame_id, **payload}, use_bin_type=True))


async def _publish_status(
    room: Room, *, connected: bool, problem: str | None, game: str | None = None
) -> None:
    room.status.connected_to_game = connected
    room.status.game = (game or GAME_ID) if connected else None
    room.status.problem = problem
    await room.broadcast(
        _encode(
            "agent_status",
            {"connected_to_game": connected, "game": room.status.game, "problem": problem},
        )
    )


def mount_api() -> None:
    """Attach the recorded-session endpoints.

    They live in the agent because reading .ld files is agent territory, but
    they are served by the hub the strategist is already talking to.
    """
    if not any(route.path.startswith("/api/logs") for route in app.routes):  # type: ignore[attr-defined]
        app.include_router(ld_router)


def stream_forever(room: Room, config: ServeConfig) -> None:
    """Blocking wrapper for the desktop window, which runs this on its own thread."""
    asyncio.run(_stream(room, config))


async def _replay(room: Room, config: ServeConfig) -> None:
    """Play a recorded session into the room at its original pace."""
    assert config.replay is not None
    source = LdReplaySource(config.replay, rate_hz=config.rate_hz)
    session = source.session

    room.channels = sorted(session.available)
    room.rate_hz = config.rate_hz
    await _publish_status(
        room,
        connected=True,
        problem=(
            f"Запись: {config.replay.stem} — {session.meta.venue}, "
            f"{session.meta.driver}. Это не живая машина."
        ),
        game=REPLAY_GAME_ID,
    )

    period = 1.0 / config.rate_hz
    batch: list[dict[str, object]] = []
    last_flush = asyncio.get_running_loop().time()

    while True:
        frame = source.poll()
        if frame is None:
            source.rewind()
            continue

        batch.append({"t": frame.t, "v": frame.values})
        now = asyncio.get_running_loop().time()
        if now - last_flush >= BATCH_INTERVAL_S:
            await room.broadcast(_encode("samples", {"count": len(batch), "rows": batch}))
            batch = []
            last_flush = now

        await asyncio.sleep(period)


async def _stream(room: Room, config: ServeConfig) -> None:
    if config.replay is not None:
        await _replay(room, config)
        return

    provider = LmuProvider()
    period = 1.0 / config.rate_hz

    while True:
        try:
            provider.open()
        except ProviderUnavailableError as exc:
            await _publish_status(room, connected=False, problem=str(exc))
            await asyncio.sleep(RETRY_INTERVAL_S)
            continue

        room.channels = sorted(provider.capabilities().available)
        room.rate_hz = config.rate_hz
        await _publish_status(room, connected=True, problem=None)

        try:
            await _pump(room, provider, period)
        except ProviderUnavailableError as exc:
            await _publish_status(room, connected=False, problem=str(exc))
        except TornReadError as exc:
            await _publish_status(room, connected=False, problem=str(exc))
        finally:
            provider.close()

        await asyncio.sleep(RETRY_INTERVAL_S)


async def _pump(room: Room, provider: LmuProvider, period: float) -> None:
    """Poll and broadcast until the source goes away."""
    batch: list[dict[str, object]] = []
    last_flush = asyncio.get_running_loop().time()

    while True:
        frame = provider.poll()
        if frame is not None:
            batch.append({"t": frame.t, "v": frame.values})

        now = asyncio.get_running_loop().time()
        if batch and now - last_flush >= BATCH_INTERVAL_S:
            await room.broadcast(_encode("samples", {"count": len(batch), "rows": batch}))
            batch.clear()
            last_flush = now

        await asyncio.sleep(period)


async def _serve(config: ServeConfig) -> None:
    room = registry.create(token=config.token, code=config.room_code)
    room.rate_hz = config.rate_hz

    server = uvicorn.Server(
        uvicorn.Config(app, host=config.host, port=config.port, log_level="warning")
    )

    streamer = asyncio.create_task(_stream(room, config))
    try:
        await server.serve()
    finally:
        streamer.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await streamer


def run(config: ServeConfig) -> int:
    # flush on every line: stdout is block-buffered when it is not a terminal,
    # and the driver needs the room code before the session starts, not after
    # the process exits.
    def say(line: str = "") -> None:
        print(line, flush=True)

    mount_api()

    build = find_web_build()
    if build is None or not mount_web_ui(build):
        say(
            "The web UI build was not found. Telemetry will still stream over "
            "the WebSocket, but there is no page to open.\n"
            "Build it with: npm run build --workspace @pitwall/web"
        )

    say(f"Room code : {config.room_code}")
    say(f"Listening : http://{config.host}:{config.port}")
    if config.token:
        say("A token is required to join.")
    say()
    say("Give the strategist the address above and the room code.")
    say("Ctrl+C to stop.")

    asyncio.run(_serve(config))
    return 0
