"""The probe's whole job is to not report false positives."""

from __future__ import annotations

import sys

import pytest
from pitwall_agent.shm_probe import probe

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows shared memory")


def test_absent_section_reports_missing() -> None:
    """The naive mmap(-1, tagname=...) implementation creates the section and
    reports success here. This name cannot plausibly exist."""
    result = probe("$PitWall_NoSuchSection_a4f1c9$")
    assert result.exists is False
    assert result.detail == "not published"


def test_probe_does_not_create_the_section() -> None:
    name = "$PitWall_ProbeMustNotCreate_7d2e$"
    assert probe(name).exists is False
    assert probe(name).exists is False
