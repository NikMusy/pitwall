"""Session browsing and channel data for the analysis view.

Decimation happens here, not in the browser. A two-hour log holds millions of
samples per channel and the screen has about fifteen hundred pixel columns, so
sending the raw arrays would move a hundred times more data than can be drawn.

The reduction is min/max per column, not sampling: for each pixel column both
the lowest and highest value in that span are kept. Picking every Nth sample
would drop the brake pressure spike that the engineer opened the log to find.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from pitwall_agent.ld.logs import list_logs
from pitwall_agent.ld.mapping import LD_MAPPINGS
from pitwall_agent.ld.reader import InvalidLdFileError, read_ld

router = APIRouter(prefix="/api")

MAX_COLUMNS = 4000


@dataclass(frozen=True, slots=True)
class LoadedChannel:
    key: str
    unit: str
    rate_hz: int
    values: list[float]


def _log_by_id(log_id: str) -> Path:
    for entry in list_logs():
        if entry.label == log_id:
            return entry.path
    raise HTTPException(status_code=404, detail=f"No log named {log_id!r}")


@router.get("/logs")
def get_logs() -> list[dict[str, Any]]:
    return [
        {
            "id": entry.label,
            "recorded_at": entry.recorded_at.isoformat(timespec="seconds"),
            "size_bytes": entry.size_bytes,
        }
        for entry in list_logs()
    ]


@router.get("/logs/{log_id}")
def get_log(log_id: str) -> dict[str, Any]:
    path = _log_by_id(log_id)
    try:
        meta, channels = read_ld(path)
    except InvalidLdFileError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    by_name = {channel.name: channel for channel in channels}
    available = {
        key: by_name[mapping.ld_name]
        for key, mapping in LD_MAPPINGS.items()
        if mapping.ld_name in by_name and by_name[mapping.ld_name].rate_hz > 0
    }

    duration = max((channel.duration_s for channel in available.values()), default=0.0)

    return {
        "id": log_id,
        "driver": meta.driver,
        "venue": meta.venue,
        "date": meta.date,
        "time": meta.time,
        "duration_s": duration,
        "channels": [
            {"key": key, "unit": channel.unit, "rate_hz": channel.rate_hz}
            for key, channel in sorted(available.items())
        ],
        "laps": _laps(available.get("lap"), available.get("distance")),
    }


def _laps(lap_channel: Any, distance_channel: Any) -> list[dict[str, Any]]:
    """Lap boundaries taken from where the log's own lap counter changes.

    Derived from the recorded counter rather than from distance crossing zero,
    because the counter is what the game itself considered a lap.
    """
    if lap_channel is None or lap_channel.rate_hz <= 0:
        return []

    samples = lap_channel.samples
    rate = lap_channel.rate_hz
    laps: list[dict[str, Any]] = []
    start_index = 0

    for index in range(1, len(samples)):
        if samples[index] != samples[index - 1]:
            laps.append(
                {
                    "number": int(samples[index - 1]),
                    "start_s": start_index / rate,
                    "end_s": index / rate,
                }
            )
            start_index = index

    if start_index < len(samples) - 1:
        laps.append(
            {
                "number": int(samples[-1]),
                "start_s": start_index / rate,
                "end_s": len(samples) / rate,
            }
        )

    return [lap for lap in laps if lap["end_s"] - lap["start_s"] > 1.0]


@router.get("/logs/{log_id}/channels")
def get_channels(
    log_id: str,
    keys: str = Query(..., description="Comma-separated schema channel keys"),
    from_s: float = Query(0.0, alias="from"),
    to_s: float | None = Query(None, alias="to"),
    columns: int = Query(1500, le=MAX_COLUMNS, ge=1),
) -> dict[str, Any]:
    path = _log_by_id(log_id)
    meta, channels = read_ld(path)
    by_name = {channel.name: channel for channel in channels}

    requested = [key.strip() for key in keys.split(",") if key.strip()]
    result: dict[str, Any] = {}

    for key in requested:
        mapping = LD_MAPPINGS.get(key)
        source = by_name.get(mapping.ld_name) if mapping else None
        if mapping is None or source is None:
            # Absent stays absent. The chart draws a gap and says so rather
            # than a flat line at zero.
            result[key] = None
            continue

        end_s = to_s if to_s is not None else source.duration_s
        start_index = max(0, int(from_s * source.rate_hz))
        end_index = min(len(source.samples), int(end_s * source.rate_hz))
        if end_index <= start_index:
            result[key] = None
            continue

        window = source.samples[start_index:end_index]
        times, mins, maxs = _min_max_decimate(
            window, source.rate_hz, from_s, min(columns, len(window))
        )
        convert = mapping.convert
        result[key] = {
            "unit": mapping.ld_name,
            "t": times,
            "min": [convert(value) for value in mins],
            "max": [convert(value) for value in maxs],
        }

    return {"id": log_id, "venue": meta.venue, "channels": result}


def _min_max_decimate(
    window: Any, rate_hz: int, t0: float, columns: int
) -> tuple[list[float], list[float], list[float]]:
    total = len(window)
    per_column = max(1, total // columns)

    times: list[float] = []
    mins: list[float] = []
    maxs: list[float] = []

    for column_start in range(0, total, per_column):
        chunk = window[column_start : column_start + per_column]
        if len(chunk) == 0:
            continue
        times.append(t0 + column_start / rate_hz)
        mins.append(float(chunk.min()))
        maxs.append(float(chunk.max()))

    return times, mins, maxs
