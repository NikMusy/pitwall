"""Hub entry point."""

from __future__ import annotations

import argparse

import uvicorn

DEFAULT_PORT = 8420


def main() -> int:
    parser = argparse.ArgumentParser(prog="pitwall-hub")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help=(
            "Bind address. Localhost by default. To let a remote strategist in over "
            "Tailscale, bind the tailnet address rather than 0.0.0.0."
        ),
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    uvicorn.run("pitwall_hub.app:app", host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
