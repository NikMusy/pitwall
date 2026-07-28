"""Agent entry point."""

from __future__ import annotations

import argparse
import sys

from pitwall_agent import serve as serve_module
from pitwall_agent.rooms_util import normalise_room_code
from pitwall_agent.shm_probe import probe
from pitwall_agent.tailnet import detect as detect_tailnet

# Published by rFactor2SharedMemoryMapPlugin64.dll, which LMU and rF2 share.
RF2_SECTIONS = {
    "$rFactor2SMMP_Telemetry$": "per-vehicle physics",
    "$rFactor2SMMP_Scoring$": "all cars, timing and pit state",
    "$rFactor2SMMP_Extended$": "plugin and session state",
    "$rFactor2SMMP_Rules$": "FCY, safety car, pit rules",
}

ACC_SECTIONS = {
    "Local\\acpmf_physics": "ACC physics",
    "Local\\acpmf_graphics": "ACC session and lap state",
    "Local\\acpmf_static": "ACC car and track identity",
}

DEFAULT_PORT = 8420
DEFAULT_RATE_HZ = 50


def cmd_doctor() -> int:
    """Report which telemetry sources are reachable right now.

    Reports only what it can verify. A section that is absent is absent — no
    guessing at why beyond what the OS actually told us.
    """
    found_any = False

    for title, sections in (("LMU / rFactor 2", RF2_SECTIONS), ("ACC", ACC_SECTIONS)):
        print(f"\n{title}")
        for name, purpose in sections.items():
            result = probe(name)
            mark = "ok  " if result.exists else "MISS"
            found_any = found_any or result.exists
            print(f"  [{mark}] {name:<32} {result.detail:<20} ({purpose})")

    identity = detect_tailnet()
    print("\nTailscale")
    if identity is None:
        print("  [MISS] not available — the strategist cannot reach this machine")
    else:
        print(f"  [ok  ] {identity.ip}  {identity.dns_name or ''}")

    if not found_any:
        print(
            "\nNo telemetry sections are published.\n"
            "If the game is running, the shared memory plugin is probably not "
            "installed or not enabled — see docs/lmu-setup.md.",
            file=sys.stderr,
        )
        return 1

    return 0


def cmd_serve(args: argparse.Namespace, *, windowed: bool) -> int:
    host = args.host
    if host is None:
        identity = detect_tailnet()
        if identity is None:
            if not windowed:
                print(
                    "Could not determine the Tailscale address, and no --host was given.\n"
                    "Start Tailscale, or pass --host explicitly.",
                    file=sys.stderr,
                )
                return 1
            # The window is still useful without a tailnet: the driver can
            # watch their own car even if no strategist can reach them.
            host = "127.0.0.1"
        else:
            host = identity.ip
            if identity.dns_name and not windowed:
                print(f"Tailnet name: {identity.dns_name}")

    config = serve_module.ServeConfig(
        host=host,
        port=args.port,
        room_code=normalise_room_code(args.room),
        token=args.token,
        rate_hz=args.rate,
    )

    if windowed:
        from pitwall_agent import desktop

        return desktop.run(config)
    return serve_module.run(config)


def _add_serve_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--host",
        default=None,
        help="Bind address. Defaults to this machine's Tailscale address.",
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--room", default=None, help="Room code. Generated when omitted.")
    parser.add_argument("--token", default=None, help="Optional shared secret required to join.")
    parser.add_argument("--rate", type=int, default=DEFAULT_RATE_HZ)


def main() -> int:
    parser = argparse.ArgumentParser(prog="PitWall", description=__doc__)
    # No required subcommand: double-clicking the executable passes no
    # arguments at all, and that has to open the window rather than print usage.
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("doctor", help="Check which telemetry sources are reachable")
    _add_serve_arguments(sub.add_parser("serve", help="Headless: stream without opening a window"))
    _add_serve_arguments(sub.add_parser("app", help="Open the desktop window (default)"))
    _add_serve_arguments(parser)

    args = parser.parse_args()
    if args.command == "doctor":
        return cmd_doctor()
    if args.command == "serve":
        return cmd_serve(args, windowed=False)
    return cmd_serve(args, windowed=True)


if __name__ == "__main__":
    raise SystemExit(main())
