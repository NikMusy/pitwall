"""Map Le Mans Ultimate .ld channel names onto schema keys.

Only conversions are applied, never invention: a schema channel with no source
in the log stays absent. `.ld` has no gear and no usable world position, so the
track map cannot be built from a log — that needs live shared memory.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

KELVIN_OFFSET = 273.15
G = 9.80665
MM_PER_M = 1000.0
KMH_PER_MS = 3.6


@dataclass(frozen=True, slots=True)
class Mapping:
    ld_name: str
    convert: Callable[[float], float]


def _identity(value: float) -> float:
    return value


def _percent_to_ratio(value: float) -> float:
    return value / 100.0


def _celsius_to_kelvin(value: float) -> float:
    return value + KELVIN_OFFSET


def _kmh_to_ms(value: float) -> float:
    return value / KMH_PER_MS


def _g_to_ms2(value: float) -> float:
    return value * G


def _mm_to_m(value: float) -> float:
    return value / MM_PER_M


CORNERS = (("fl", "FL"), ("fr", "FR"), ("rl", "RL"), ("rr", "RR"))
BANDS = (("i", "Inner"), ("m", "Centre"), ("o", "Outer"))


def _build() -> dict[str, Mapping]:
    mappings: dict[str, Mapping] = {
        "time": Mapping("Session Elapsed Time", _identity),
        "lap": Mapping("Lap Number", _identity),
        "distance": Mapping("Lap Distance", _identity),
        "speed": Mapping("Ground Speed", _kmh_to_ms),
        "rpm": Mapping("Engine RPM", _identity),
        # "Throttle Pos" is the raw pedal; the filtered channel is what the car
        # actually acted on, which is what matches live shared memory.
        "throttle": Mapping("Throttle Pos Filtered", _percent_to_ratio),
        "brake": Mapping("Brake Pos Filtered", _percent_to_ratio),
        "clutch": Mapping("Clutch Pos Filtered", _percent_to_ratio),
        "steering": Mapping("Steering Filtered", _percent_to_ratio),
        "accel_lat": Mapping("G Force Lat", _g_to_ms2),
        "accel_long": Mapping("G Force Long", _g_to_ms2),
        "accel_vert": Mapping("G Force Vert", _g_to_ms2),
        "pitch": Mapping("Body Pitch", _identity),
        "roll": Mapping("Body Roll", _identity),
        "fuel_level": Mapping("Fuel Level", _identity),
        "water_temp": Mapping("Eng Water Temp", _celsius_to_kelvin),
        "oil_temp": Mapping("Eng Oil Temp", _celsius_to_kelvin),
        "air_temp": Mapping("Ambient Temperature", _celsius_to_kelvin),
        "track_temp": Mapping("Track Temperature", _celsius_to_kelvin),
        "rain_pct": Mapping("Raining", _percent_to_ratio),
        "wind_speed": Mapping("Wind Speed", _identity),
        "wind_dir": Mapping("Wind Heading", _identity),
    }

    for key, label in CORNERS:
        mappings[f"brake_temp_{key}"] = Mapping(f"Brake Temp {label}", _celsius_to_kelvin)
        mappings[f"tyre_press_{key}"] = Mapping(f"Tyre Pressure {label}", _identity)
        # The log already counts wear up from zero, matching the schema, so
        # this one is not inverted the way live shared memory is.
        mappings[f"tyre_wear_{key}"] = Mapping(f"Tyre Wear {label}", _percent_to_ratio)
        mappings[f"ride_height_{key}"] = Mapping(f"Ride Height {label}", _mm_to_m)
        mappings[f"susp_travel_{key}"] = Mapping(f"Susp Pos {label}", _mm_to_m)

        for band_key, band_label in BANDS:
            mappings[f"tyre_temp_{key}_{band_key}"] = Mapping(
                f"Tyre Temp {label} {band_label}", _celsius_to_kelvin
            )

    return mappings


LD_MAPPINGS = _build()

# Present in the schema but absent from LMU logs. Listed so the gap is a stated
# fact rather than something discovered later by a confused engineer.
NOT_IN_LD = (
    "gear",
    "pos_x",
    "pos_y",
    "pos_z",
    "yaw",
    "drs",
    "ers_deploy",
    "ers_store",
    "abs_active",
    "tc_active",
    "damage_front",
    "damage_rear",
    "damage_left",
    "damage_right",
    "damage_engine",
    "damage_gearbox",
    "brake_pressure_fl",
    "brake_pressure_fr",
    "brake_pressure_rl",
    "brake_pressure_rr",
    "fuel_used_lap",
)
