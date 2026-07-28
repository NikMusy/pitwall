"""MoTeC .ld reader.

Implemented from the open description of the format. No MoTeC code or headers
are used. Verified against Le Mans Ultimate logs, which is the only dialect we
claim to support — other loggers write the same container with different
channel names and rates.

Layout: a fixed header points at a singly linked list of channel descriptors,
each of which points at its own block of samples. Values are stored as scaled
integers or floats and are decoded with the per-channel scale, multiplier,
decimal-place and shift factors.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

import numpy as np

HEADER_FORMAT = (
    "<"
    "I4x"  # 0x00 marker
    "II"  # 0x08 channel meta pointer, 0x0C channel data pointer
    "20x"
    "I"  # 0x24 event pointer
    "24x"
    "HHH"  # 0x40
    "I"  # 0x46 device serial
    "8s"  # device type
    "HH"
    "I"
    "4x"
    "16s"  # 0x5E date
    "16x"
    "16s"  # 0x7E time
    "16x"
    "64s"  # 0x9E driver
    "64s"  # 0xDE vehicle
    "64x"
    "64s"  # 0x15E venue
)

CHANNEL_FORMAT = (
    "<"
    "IIII"  # previous meta, next meta, data pointer, sample count
    "HH"  # counter, type group
    "HH"  # width, rate in Hz
    "hhhh"  # shift, multiplier, scale, decimal places
    "32s"  # name
    "8s"  # short name
    "12s"  # unit
    "40x"
)
CHANNEL_SIZE = struct.calcsize(CHANNEL_FORMAT)

TYPE_FLOAT = 0x07
TYPE_INTEGER = (0x00, 0x03, 0x05)

SampleDtype = type[np.float16] | type[np.float32] | type[np.int16] | type[np.int32]

FLOAT_WIDTHS: dict[int, SampleDtype] = {2: np.float16, 4: np.float32}
INTEGER_WIDTHS: dict[int, SampleDtype] = {2: np.int16, 4: np.int32}


class InvalidLdFileError(ValueError):
    """The file is not a readable .ld container."""


@dataclass(frozen=True, slots=True)
class LdMeta:
    driver: str
    vehicle: str
    venue: str
    date: str
    time: str


@dataclass(slots=True)
class LdChannel:
    name: str
    short_name: str
    unit: str
    rate_hz: int
    samples: np.ndarray

    @property
    def duration_s(self) -> float:
        if self.rate_hz <= 0:
            return 0.0
        return len(self.samples) / self.rate_hz


def _text(raw: bytes) -> str:
    trimmed = raw.partition(b"\0")[0]
    try:
        return trimmed.decode("utf-8").strip()
    except UnicodeDecodeError:
        # Some logs carry Latin-1 in the driver field; a name is not worth
        # failing the whole read over.
        return trimmed.decode("latin-1", "replace").strip()


def _sample_dtype(type_group: int, width: int) -> SampleDtype | None:
    if type_group == TYPE_FLOAT:
        return FLOAT_WIDTHS.get(width)
    if type_group in TYPE_INTEGER:
        return INTEGER_WIDTHS.get(width)
    return None


def read_ld(path: Path | str) -> tuple[LdMeta, list[LdChannel]]:
    raw = Path(path).read_bytes()

    if len(raw) < struct.calcsize(HEADER_FORMAT):
        raise InvalidLdFileError(f"{path}: too short to contain a header")

    header = struct.unpack_from(HEADER_FORMAT, raw)
    meta = LdMeta(
        driver=_text(header[14]),
        vehicle=_text(header[15]),
        venue=_text(header[16]),
        date=_text(header[12]),
        time=_text(header[13]),
    )

    channels: list[LdChannel] = []
    pointer = header[1]
    visited: set[int] = set()

    # The list is singly linked with absolute offsets. A corrupt file can point
    # back at itself, so walking it needs a cycle guard rather than trust.
    while pointer and pointer not in visited and pointer + CHANNEL_SIZE <= len(raw):
        visited.add(pointer)
        (
            _previous,
            next_pointer,
            data_pointer,
            sample_count,
            _counter,
            type_group,
            width,
            rate_hz,
            shift,
            multiplier,
            scale,
            decimals,
            name,
            short_name,
            unit,
        ) = struct.unpack_from(CHANNEL_FORMAT, raw, pointer)

        dtype = _sample_dtype(type_group, width)
        readable = (
            dtype is not None
            and sample_count > 0
            and scale != 0
            and data_pointer + sample_count * width <= len(raw)
        )

        if readable:
            assert dtype is not None
            stored = np.frombuffer(raw, dtype=dtype, count=sample_count, offset=data_pointer)
            decoded = stored.astype(np.float64) / scale * 10.0**-decimals * multiplier + shift
            channels.append(
                LdChannel(
                    name=_text(name),
                    short_name=_text(short_name),
                    unit=_text(unit),
                    rate_hz=rate_hz,
                    samples=decoded,
                )
            )

        pointer = next_pointer

    if not channels:
        raise InvalidLdFileError(f"{path}: no readable channels")

    return meta, channels
