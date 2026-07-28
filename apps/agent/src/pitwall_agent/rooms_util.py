"""Room code handling on the agent side."""

from __future__ import annotations

from pitwall_hub.rooms import ROOM_ALPHABET, generate_room_code, is_valid_room_code


def normalise_room_code(code: str | None) -> str:
    """Accept a user-supplied code, or generate one.

    An invalid code is rejected rather than silently replaced: a driver who
    typed the code they already gave the strategist needs to hear that it did
    not take, not discover it mid-session.
    """
    if code is None:
        return generate_room_code()

    candidate = code.strip().upper()
    if not is_valid_room_code(candidate):
        raise SystemExit(
            f"Invalid room code {code!r}: expected six characters from "
            f"{ROOM_ALPHABET} (no vowels, no 0/1)."
        )
    return candidate
