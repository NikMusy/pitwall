"""Agent entry point."""

from __future__ import annotations

import argparse
import sys

from pitwall_agent.shm_probe import probe

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

    if not found_any:
        print(
            "\nNo telemetry sections are published.\n"
            "If the game is running, the shared memory plugin is probably not "
            "installed or not enabled — see docs/lmu-setup.md.",
            file=sys.stderr,
        )
        return 1

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="pitwall-agent", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Check which telemetry sources are reachable")

    args = parser.parse_args()
    if args.command == "doctor":
        return cmd_doctor()

    parser.error(f"unknown command {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
