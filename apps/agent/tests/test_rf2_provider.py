"""Channel mapping tests.

These build shared memory structs in memory and check what comes out the other
side. That is not synthetic telemetry standing in for real data — nothing here
is presented as a lap. It is the only way to test a mapper without the game
running, and it catches the conversions that are easy to get backwards.
"""

from __future__ import annotations

import math

import pytest
from pitwall_agent.provider import unknown_channels
from pitwall_agent.rf2.provider import _MAPPED_KEYS, KELVIN_OFFSET, LmuProvider
from pitwall_agent.rf2.structs import rF2Scoring, rF2VehicleScoring, rF2VehicleTelemetry


def _scoring_with(ambient_c: float = 20.0, track_c: float = 30.0) -> rF2Scoring:
    scoring = rF2Scoring()
    scoring.mScoringInfo.mAmbientTemp = ambient_c
    scoring.mScoringInfo.mTrackTemp = track_c
    return scoring


def test_every_mapped_key_exists_in_the_schema() -> None:
    assert unknown_channels(_MAPPED_KEYS) == set()


def test_emitted_keys_all_exist_in_the_schema() -> None:
    provider = LmuProvider()
    values = provider._map_values(rF2VehicleTelemetry(), rF2VehicleScoring(), _scoring_with())
    assert unknown_channels(values) == set()


def test_tyre_wear_is_inverted() -> None:
    """rF2 reports 1.0 for a new tyre. The schema says 0 is new."""
    car = rF2VehicleTelemetry()
    car.mWheels[0].mWear = 1.0
    car.mWheels[1].mWear = 0.75

    values = LmuProvider()._map_values(car, rF2VehicleScoring(), _scoring_with())

    assert values["tyre_wear_fl"] == pytest.approx(0.0)
    assert values["tyre_wear_fr"] == pytest.approx(0.25)


def test_celsius_channels_are_converted_but_kelvin_ones_are_not() -> None:
    car = rF2VehicleTelemetry()
    car.mEngineWaterTemp = 90.0  # rF2 gives Celsius here
    car.mWheels[0].mBrakeTemp = 600.0  # and Kelvin here

    values = LmuProvider()._map_values(car, rF2VehicleScoring(), _scoring_with(ambient_c=18.0))

    assert values["water_temp"] == pytest.approx(90.0 + KELVIN_OFFSET)
    assert values["air_temp"] == pytest.approx(18.0 + KELVIN_OFFSET)
    assert values["brake_temp_fl"] == pytest.approx(600.0)


def test_speed_is_the_velocity_magnitude() -> None:
    car = rF2VehicleTelemetry()
    car.mLocalVel.x = 3.0
    car.mLocalVel.y = 0.0
    car.mLocalVel.z = 4.0

    values = LmuProvider()._map_values(car, rF2VehicleScoring(), _scoring_with())

    assert values["speed"] == pytest.approx(5.0)


def test_unavailable_channels_are_null_not_zero() -> None:
    """rF2 has no DRS or ERS in this buffer. Zero would read as 'closed' and
    'empty battery', which are claims we cannot make."""
    values = LmuProvider()._map_values(rF2VehicleTelemetry(), rF2VehicleScoring(), _scoring_with())

    for key in ("drs", "ers_deploy", "ers_store", "abs_active", "tc_active"):
        assert values[key] is None


def test_fuel_used_is_null_until_a_lap_boundary_is_seen() -> None:
    provider = LmuProvider()
    car = rF2VehicleTelemetry()
    car.mLapNumber = 4
    car.mFuel = 60.0

    first = provider._map_values(car, rF2VehicleScoring(), _scoring_with())
    assert first["fuel_used_lap"] is None

    car.mFuel = 57.5
    second = provider._map_values(car, rF2VehicleScoring(), _scoring_with())
    assert second["fuel_used_lap"] == pytest.approx(2.5)


def test_fuel_used_resets_on_a_new_lap() -> None:
    provider = LmuProvider()
    car = rF2VehicleTelemetry()
    car.mLapNumber = 4
    car.mFuel = 60.0
    provider._map_values(car, rF2VehicleScoring(), _scoring_with())

    car.mLapNumber = 5
    car.mFuel = 57.0
    assert provider._map_values(car, rF2VehicleScoring(), _scoring_with())["fuel_used_lap"] is None

    car.mFuel = 54.0
    later = provider._map_values(car, rF2VehicleScoring(), _scoring_with())
    assert later["fuel_used_lap"] == pytest.approx(3.0)


def test_yaw_comes_from_the_forward_axis() -> None:
    car = rF2VehicleTelemetry()
    # Forward pointing along +x is a quarter turn from pointing along +z.
    car.mOri[2].x = 1.0
    car.mOri[2].z = 0.0

    values = LmuProvider()._map_values(car, rF2VehicleScoring(), _scoring_with())

    assert values["yaw"] == pytest.approx(math.pi / 2)
