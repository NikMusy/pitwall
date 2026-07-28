"""Find the machine's Tailscale address.

Binding 0.0.0.0 would expose the hub on every interface including whatever
network the driver happens to be on. Binding the tailnet address specifically
means only the tailnet can reach it.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

WINDOWS_DEFAULT = Path(r"C:\Program Files\Tailscale\tailscale.exe")


@dataclass(frozen=True)
class TailnetIdentity:
    ip: str
    dns_name: str | None


def _executable() -> str | None:
    found = shutil.which("tailscale")
    if found:
        return found
    if WINDOWS_DEFAULT.is_file():
        return str(WINDOWS_DEFAULT)
    return None


def detect() -> TailnetIdentity | None:
    """Return this machine's tailnet identity, or None if unavailable."""
    executable = _executable()
    if executable is None:
        return None

    try:
        raw = subprocess.run(
            [executable, "status", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        ).stdout
    except (subprocess.SubprocessError, OSError):
        return None

    try:
        status = json.loads(raw)
        self_node = status["Self"]
        ips = self_node.get("TailscaleIPs") or []
    except (json.JSONDecodeError, KeyError, TypeError):
        return None

    ipv4 = next((ip for ip in ips if ":" not in ip), None)
    if ipv4 is None:
        return None

    dns_name = (self_node.get("DNSName") or "").rstrip(".") or None
    return TailnetIdentity(ip=ipv4, dns_name=dns_name)
