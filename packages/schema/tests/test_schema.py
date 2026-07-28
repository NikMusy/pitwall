"""The schema is load-bearing: every other module trusts these keys."""

from __future__ import annotations

import pytest
from pitwall_codegen import build, expand_channels
from pitwall_schema import CHANNELS, PROTOCOL_VERSION

# From SPEC section 5. A provider that cannot supply one of these must report
# null, so the key still has to exist.
CORE_KEYS = [
    "time",
    "distance",
    "lap",
    "lap_time",
    "speed",
    "rpm",
    "gear",
    "throttle",
    "brake",
    "clutch",
    "steering",
    "pos_x",
    "pos_y",
    "pos_z",
    "yaw",
    "pitch",
    "roll",
    "accel_lat",
    "accel_long",
    "accel_vert",
    "fuel_level",
    "fuel_used_lap",
    "water_temp",
    "oil_temp",
    "drs",
    "ers_deploy",
    "ers_store",
    "abs_active",
    "tc_active",
    "air_temp",
    "track_temp",
    "rain_pct",
    "wind_speed",
    "wind_dir",
]

CORNERS = ["fl", "fr", "rl", "rr"]
BANDS = ["i", "m", "o"]


@pytest.mark.parametrize("key", CORE_KEYS)
def test_core_channel_present(key: str) -> None:
    assert key in CHANNELS


@pytest.mark.parametrize("corner", CORNERS)
@pytest.mark.parametrize("band", BANDS)
def test_tyre_temp_expansion(corner: str, band: str) -> None:
    assert f"tyre_temp_{corner}_{band}" in CHANNELS


@pytest.mark.parametrize("corner", CORNERS)
@pytest.mark.parametrize(
    "prefix",
    ["tyre_press", "tyre_wear", "brake_temp", "brake_pressure", "susp_travel", "ride_height"],
)
def test_per_corner_expansion(prefix: str, corner: str) -> None:
    assert f"{prefix}_{corner}" in CHANNELS


def test_keys_are_snake_case() -> None:
    for key in CHANNELS:
        assert key == key.lower()
        assert " " not in key
        assert "{" not in key, f"unexpanded template left in {key}"


def test_every_channel_has_both_languages() -> None:
    for channel in CHANNELS.values():
        assert channel.display_en
        assert channel.display_ru


def test_ratio_channels_declare_no_bare_percent_storage() -> None:
    """Storage stays SI; percent is a display concern only."""
    for channel in CHANNELS.values():
        assert channel.unit != "%"


def test_expansion_rejects_duplicate_keys() -> None:
    spec = {
        "axes": {"corner": [{"id": "fl", "label": "FL"}, {"id": "fl", "label": "FL"}]},
        "channels": [
            {
                "key": "x_{corner}",
                "expand": ["corner"],
                "display": "X {corner}",
                "unit": None,
                "group": "tyres",
                "dtype": "f32",
                "rate_hz": 1,
            }
        ],
    }
    with pytest.raises(ValueError, match="duplicate channel key"):
        expand_channels(spec)


def test_protocol_version_is_positive() -> None:
    assert PROTOCOL_VERSION >= 1


def test_generated_files_are_current() -> None:
    """Guards against hand-edited generated files. CI runs the same check."""
    for path, content in build().items():
        assert path.exists(), f"{path} has never been generated"
        assert path.read_text(encoding="utf-8") == content, (
            f"{path} is stale — run `uv run pitwall-codegen`"
        )
