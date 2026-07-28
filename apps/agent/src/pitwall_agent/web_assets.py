"""Locate the built web UI.

Two layouts have to work: the repo checkout during development, and the
PyInstaller bundle where the build is copied next to the executable.
"""

from __future__ import annotations

import sys
from pathlib import Path


def find_web_build() -> Path | None:
    for candidate in _candidates():
        if (candidate / "index.html").is_file():
            return candidate
    return None


def _candidates() -> list[Path]:
    paths: list[Path] = []

    bundle = getattr(sys, "_MEIPASS", None)
    if bundle is not None:
        paths.append(Path(bundle) / "web")

    # apps/agent/src/pitwall_agent/web_assets.py -> repo root
    repo_root = Path(__file__).resolve().parents[4]
    paths.append(repo_root / "apps" / "web" / "dist")

    return paths
