"""Replay a recorded .ld log as if it were arriving live.

Channels in a log run at different rates — 1 Hz for weather, 100 Hz for
suspension. Frames are emitted on one clock and each channel is read at the
sample covering that instant. No interpolation: showing a value the logger
never recorded would be inventing data, and holding the last real sample is
what the logger itself means by a lower rate.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pitwall_agent.ld.mapping import LD_MAPPINGS
from pitwall_agent.ld.reader import LdChannel, LdMeta, read_ld
from pitwall_agent.provider import Capabilities, Frame

GAME_ID = "lmu-replay"


@dataclass(frozen=True, slots=True)
class ReplaySession:
    meta: LdMeta
    duration_s: float
    available: frozenset[str]


class LdReplaySource:
    """Turns a log file into frames at a chosen wall-clock rate."""

    def __init__(self, path: Path | str, rate_hz: int = 50) -> None:
        self._path = Path(path)
        self._rate_hz = rate_hz
        self._meta, channels = read_ld(self._path)

        by_name: dict[str, LdChannel] = {channel.name: channel for channel in channels}
        self._resolved: dict[str, tuple[LdChannel, object]] = {}
        for key, mapping in LD_MAPPINGS.items():
            channel = by_name.get(mapping.ld_name)
            if channel is not None and channel.rate_hz > 0:
                self._resolved[key] = (channel, mapping.convert)

        self._duration = max(
            (channel.duration_s for channel, _ in self._resolved.values()), default=0.0
        )
        self._index = 0

    @property
    def session(self) -> ReplaySession:
        return ReplaySession(
            meta=self._meta,
            duration_s=self._duration,
            available=frozenset(self._resolved),
        )

    def capabilities(self) -> Capabilities:
        return Capabilities(
            game=GAME_ID,
            available=frozenset(self._resolved),
            rate_hz=self._rate_hz,
            all_cars=False,
        )

    def sample_at(self, t: float) -> dict[str, float | int | bool | None]:
        values: dict[str, float | int | bool | None] = {}
        for key, (channel, convert) in self._resolved.items():
            index = int(t * channel.rate_hz)
            if 0 <= index < len(channel.samples):
                values[key] = float(convert(float(channel.samples[index])))  # type: ignore[operator]
            else:
                values[key] = None
        return values

    def poll(self) -> Frame | None:
        """Next frame, or None once the log has played out."""
        t = self._index / self._rate_hz
        if t > self._duration:
            return None

        self._index += 1
        return Frame(t=t, values=self.sample_at(t))

    def rewind(self) -> None:
        self._index = 0
