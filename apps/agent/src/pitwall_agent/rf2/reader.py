"""Read an rF2 shared memory buffer without tearing.

The plugin double-buffers: it increments mVersionUpdateBegin before writing and
mVersionUpdateEnd after. A snapshot where the two disagree was taken mid-write
and mixes bytes from two different physics frames. Such a frame is internally
inconsistent but every individual value in it still looks reasonable, so it
cannot be spotted downstream. It has to be rejected here.
"""

from __future__ import annotations

import ctypes
import mmap

from pitwall_agent.provider import ProviderUnavailableError
from pitwall_agent.rf2.structs import rF2MappedBufferVersionBlock
from pitwall_agent.shm_probe import probe

# The window is microseconds wide; a handful of retries is generous.
MAX_TEAR_RETRIES = 8


class TornReadError(RuntimeError):
    """Every attempt caught the writer mid-update."""


class SharedMemoryReader[BufferT: rF2MappedBufferVersionBlock]:
    def __init__(self, name: str, buffer_type: type[BufferT]) -> None:
        self._name = name
        self._buffer_type = buffer_type
        self._size = ctypes.sizeof(buffer_type)
        self._mm: mmap.mmap | None = None

    def open(self) -> None:
        # Probe first. mmap.mmap(-1, ..., tagname=name) creates the section when
        # it is absent, so mapping blind would manufacture a buffer of zeros and
        # report a healthy connection to a game that is not running.
        result = probe(self._name)
        if not result.exists:
            raise ProviderUnavailableError(
                f"{self._name}: {result.detail}. "
                "Is the game running and the shared memory plugin installed? "
                "See docs/lmu-setup.md."
            )

        self._mm = mmap.mmap(-1, self._size, tagname=self._name, access=mmap.ACCESS_READ)

    def read(self) -> BufferT:
        """Return a consistent snapshot, or raise if the writer never settled."""
        if self._mm is None:
            raise ProviderUnavailableError(f"{self._name} is not open")

        for _ in range(MAX_TEAR_RETRIES):
            self._mm.seek(0)
            snapshot = self._buffer_type.from_buffer_copy(self._mm.read(self._size))
            if snapshot.mVersionUpdateBegin == snapshot.mVersionUpdateEnd:
                return snapshot

        raise TornReadError(
            f"{self._name}: {MAX_TEAR_RETRIES} consecutive reads caught a write in progress"
        )

    def close(self) -> None:
        if self._mm is not None:
            self._mm.close()
            self._mm = None
