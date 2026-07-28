"""Layout checks for the rF2 shared memory structs.

These catch the failure mode that matters: a wrong `_pack_` or a missing field
does not raise, it shifts every subsequent field by a few bytes and yields
numbers that still look like telemetry. The offsets below are derived from
Include/rF2State.h, so a transcription slip shows up here rather than as a
mysteriously wrong brake temperature three milestones later.

Validation against a real buffer needs a recorded dump, which needs the plugin
installed — see PLAN.md, M1.
"""

from __future__ import annotations

import ctypes

from pitwall_agent.rf2.structs import (
    MAX_MAPPED_VEHICLES,
    rF2Scoring,
    rF2ScoringInfo,
    rF2Telemetry,
    rF2Vec3,
    rF2VehicleScoring,
    rF2VehicleTelemetry,
    rF2Wheel,
)


def test_vec3_is_three_doubles() -> None:
    assert ctypes.sizeof(rF2Vec3) == 24


def test_wheel_field_offsets() -> None:
    # 16 doubles precede the temperature array.
    assert rF2Wheel.mTemperature.offset == 16 * 8
    # Wear follows the three-element temperature array immediately.
    assert rF2Wheel.mWear.offset == 16 * 8 + 24
    # The byte block after mTerrainName must not gain padding under pack(4).
    assert rF2Wheel.mSurfaceType.offset == rF2Wheel.mTerrainName.offset + 16
    assert rF2Wheel.mStaticUndeflectedRadius.offset == rF2Wheel.mSurfaceType.offset + 3


def test_wheel_has_no_trailing_padding() -> None:
    expansion = rF2Wheel.mExpansion
    assert ctypes.sizeof(rF2Wheel) == expansion.offset + expansion.size


def test_vehicle_telemetry_wheels_are_last() -> None:
    wheels = rF2VehicleTelemetry.mWheels
    assert wheels.size == 4 * ctypes.sizeof(rF2Wheel)
    assert ctypes.sizeof(rF2VehicleTelemetry) == wheels.offset + wheels.size


def test_pack_four_is_in_effect() -> None:
    """Under natural alignment a c_int followed by a c_double gains 4 bytes of
    padding. mDeltaTime sitting at offset 4 is what proves pack(4)."""
    assert rF2VehicleTelemetry.mID.offset == 0
    assert rF2VehicleTelemetry.mDeltaTime.offset == 4


def test_buffers_start_with_the_version_block() -> None:
    for buffer in (rF2Telemetry, rF2Scoring):
        assert buffer.mVersionUpdateBegin.offset == 0
        assert buffer.mVersionUpdateEnd.offset == 4
        assert buffer.mBytesUpdatedHint.offset == 8


def test_vehicle_arrays_are_fully_mapped() -> None:
    assert rF2Telemetry.mVehicles.size == MAX_MAPPED_VEHICLES * ctypes.sizeof(rF2VehicleTelemetry)
    assert rF2Scoring.mVehicles.size == MAX_MAPPED_VEHICLES * ctypes.sizeof(rF2VehicleScoring)


def test_scoring_info_weather_block_offsets() -> None:
    # Weather is read every session; a shifted block here silently corrupts
    # track temperature, which the tyre model depends on.
    assert rF2ScoringInfo.mRaining.offset == rF2ScoringInfo.mDarkCloud.offset + 8
    assert rF2ScoringInfo.mAmbientTemp.offset == rF2ScoringInfo.mRaining.offset + 8
    assert rF2ScoringInfo.mTrackTemp.offset == rF2ScoringInfo.mAmbientTemp.offset + 8
    assert rF2ScoringInfo.mWind.offset == rF2ScoringInfo.mTrackTemp.offset + 8


def test_structs_round_trip_through_bytes() -> None:
    """A struct that cannot be rebuilt from its own bytes has a layout bug."""
    telemetry = rF2VehicleTelemetry()
    telemetry.mGear = 3
    telemetry.mEngineRPM = 8123.5
    telemetry.mWheels[0].mPressure = 172.5

    raw = bytes(memoryview(telemetry).cast("B"))
    restored = rF2VehicleTelemetry.from_buffer_copy(raw)

    assert restored.mGear == 3
    assert restored.mEngineRPM == 8123.5
    assert restored.mWheels[0].mPressure == 172.5
