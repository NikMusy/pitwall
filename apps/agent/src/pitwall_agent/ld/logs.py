"""Find recorded Le Mans Ultimate sessions.

LMU writes one .ld per session into its own LOG folder, named
`<date> - <time> - <track> - <session>.ld`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DEFAULT_LOG_DIRS = (
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Le Mans Ultimate\LOG"),
    Path(r"C:\Program Files\Steam\steamapps\common\Le Mans Ultimate\LOG"),
)


@dataclass(frozen=True, slots=True)
class LogFile:
    path: Path
    recorded_at: datetime
    size_bytes: int

    @property
    def label(self) -> str:
        return self.path.stem


def log_directory(override: Path | None = None) -> Path | None:
    if override is not None:
        return override if override.is_dir() else None
    return next((directory for directory in DEFAULT_LOG_DIRS if directory.is_dir()), None)


def list_logs(directory: Path | None = None) -> list[LogFile]:
    """Newest first. An unreadable entry is skipped, not guessed at."""
    root = log_directory(directory)
    if root is None:
        return []

    found: list[LogFile] = []
    for path in root.glob("*.ld"):
        try:
            stat = path.stat()
        except OSError:
            continue
        found.append(
            LogFile(
                path=path,
                recorded_at=datetime.fromtimestamp(stat.st_mtime),
                size_bytes=stat.st_size,
            )
        )

    return sorted(found, key=lambda entry: entry.recorded_at, reverse=True)


def latest_log(directory: Path | None = None) -> LogFile | None:
    return next(iter(list_logs(directory)), None)
