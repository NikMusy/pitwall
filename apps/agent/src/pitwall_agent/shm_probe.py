"""Check whether a named Windows shared memory section exists.

This deserves its own module because the obvious implementation is wrong.
`mmap.mmap(-1, size, tagname=name)` on Windows *creates* the section when it is
missing and then reports success, so a probe built on it says "present" for a
game that is not running and a plugin that was never installed. We open the
mapping explicitly instead, and a missing section reports as missing.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

FILE_MAP_READ = 0x0004
ERROR_FILE_NOT_FOUND = 2


@dataclass(frozen=True, slots=True)
class ProbeResult:
    name: str
    exists: bool
    detail: str


def probe(name: str) -> ProbeResult:
    """Report whether the named section is currently published by some process."""
    if sys.platform != "win32":
        return ProbeResult(name, False, "shared memory probing is Windows-only")

    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenFileMappingW.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR)
    kernel32.OpenFileMappingW.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL

    handle = kernel32.OpenFileMappingW(FILE_MAP_READ, False, name)
    if not handle:
        code = ctypes.get_last_error()
        if code == ERROR_FILE_NOT_FOUND:
            return ProbeResult(name, False, "not published")
        return ProbeResult(name, False, f"OpenFileMapping failed, error {code}")

    kernel32.CloseHandle(handle)
    return ProbeResult(name, True, "present")
