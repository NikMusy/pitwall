"""The contract every game integration implements.

No provider is implemented yet — see PLAN.md, M1 brings the LMU/rF2 one. The
protocol is declared here because it is the boundary the rest of the agent is
written against, not because it has multiple implementations to abstract over.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from pitwall_schema import ChannelKey


@dataclass(frozen=True, slots=True)
class Capabilities:
    """What a provider can actually deliver.

    `available` is the honest list. A channel the game does not expose is
    absent here and reported as null downstream — it is never synthesised or
    approximated to make the set look complete.
    """

    game: str
    available: frozenset[ChannelKey]
    rate_hz: int
    all_cars: bool = field(
        default=False,
        metadata={"doc": "True when the source exposes every car, not just the player's."},
    )


@dataclass(slots=True)
class Frame:
    """One instant of telemetry, already normalised to schema channel keys."""

    t: float
    values: dict[ChannelKey, float | int | bool | None]


class ProviderUnavailableError(RuntimeError):
    """The game is not running, or its telemetry source is not reachable.

    Carries a message meant for the user, not for a log file: it ends up in the
    UI, so it says what to do about it.
    """


@runtime_checkable
class TelemetryProvider(Protocol):
    def open(self) -> None:
        """Attach to the running game. Raises ProviderUnavailableError if absent."""

    def poll(self) -> Frame | None:
        """Return the next frame, or None when no new data is ready yet."""

    def close(self) -> None: ...

    def capabilities(self) -> Capabilities: ...
