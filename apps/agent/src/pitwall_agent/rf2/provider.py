"""Map rF2 / Le Mans Ultimate shared memory onto schema channels.

Unit conversions belong here, not downstream. rF2 is inconsistent about it:
tyre and brake temperatures are Kelvin, engine and ambient temperatures are
Celsius. The schema stores Kelvin throughout, so the Celsius ones are converted.
"""

from __future__ import annotations

import math

from pitwall_agent.provider import Capabilities, Frame, ProviderUnavailableError
from pitwall_agent.rf2.reader import SharedMemoryReader
from pitwall_agent.rf2.structs import (
    rF2Scoring,
    rF2Telemetry,
    rF2VehicleScoring,
    rF2VehicleTelemetry,
)

TELEMETRY_SECTION = "$rFactor2SMMP_Telemetry$"
SCORING_SECTION = "$rFactor2SMMP_Scoring$"

GAME_ID = "lmu"
KELVIN_OFFSET = 273.15

CORNERS = ("fl", "fr", "rl", "rr")
BANDS = ("i", "m", "o")


def _celsius_to_kelvin(value: float) -> float:
    return value + KELVIN_OFFSET


def _clamp_unit(value: float) -> float:
    return max(-1.0, min(1.0, value))


def _orientation_angles(vehicle: rF2VehicleTelemetry) -> tuple[float, float, float]:
    """Yaw, pitch and roll in radians from the orientation basis vectors.

    mOri holds the three world-space axes of the car. The forward axis gives
    heading and pitch, the right axis gives roll.

    The sign convention has not been checked against a recorded lap yet — the
    magnitudes are correct, a sign could be inverted. Flagged in PLAN.md M1.
    """
    right = vehicle.mOri[0]
    forward = vehicle.mOri[2]

    yaw = math.atan2(forward.x, forward.z)
    pitch = math.asin(_clamp_unit(forward.y))
    roll = math.asin(_clamp_unit(right.y))
    return yaw, pitch, roll


class LmuProvider:
    """Reads the player's car from LMU / rFactor 2 shared memory."""

    def __init__(self) -> None:
        self._telemetry = SharedMemoryReader(TELEMETRY_SECTION, rF2Telemetry)
        self._scoring = SharedMemoryReader(SCORING_SECTION, rF2Scoring)
        self._open = False
        # Fuel used per lap is a difference, so it stays null until a lap
        # boundary has actually been observed.
        self._lap_start_fuel: float | None = None
        self._current_lap: int | None = None

    def open(self) -> None:
        self._telemetry.open()
        self._scoring.open()
        self._open = True

    def close(self) -> None:
        self._telemetry.close()
        self._scoring.close()
        self._open = False

    def capabilities(self) -> Capabilities:
        return Capabilities(
            game=GAME_ID,
            available=frozenset(_MAPPED_KEYS),
            rate_hz=50,
            all_cars=True,
        )

    def poll(self) -> Frame | None:
        if not self._open:
            raise ProviderUnavailableError("provider is not open")

        scoring = self._scoring.read()
        telemetry = self._telemetry.read()

        player_scoring = self._find_player(scoring)
        if player_scoring is None:
            # In the garage or between sessions the buffers are live but hold
            # no player car. Not an error, just nothing to report yet.
            return None

        player_telemetry = self._find_vehicle(telemetry, player_scoring.mID)
        if player_telemetry is None:
            return None

        values = self._map_values(player_telemetry, player_scoring, scoring)
        return Frame(t=player_telemetry.mElapsedTime, values=values)

    @staticmethod
    def _find_player(scoring: rF2Scoring) -> rF2VehicleScoring | None:
        count = min(scoring.mScoringInfo.mNumVehicles, len(scoring.mVehicles))
        for index in range(count):
            vehicle: rF2VehicleScoring = scoring.mVehicles[index]
            if vehicle.mIsPlayer:
                return vehicle
        return None

    @staticmethod
    def _find_vehicle(telemetry: rF2Telemetry, vehicle_id: int) -> rF2VehicleTelemetry | None:
        count = min(telemetry.mNumVehicles, len(telemetry.mVehicles))
        for index in range(count):
            vehicle: rF2VehicleTelemetry = telemetry.mVehicles[index]
            if vehicle.mID == vehicle_id:
                return vehicle
        return None

    def _fuel_used_this_lap(self, lap: int, fuel: float) -> float | None:
        if self._current_lap != lap:
            self._current_lap = lap
            self._lap_start_fuel = fuel
            return None
        if self._lap_start_fuel is None:
            return None
        return self._lap_start_fuel - fuel

    def _map_values(
        self,
        car: rF2VehicleTelemetry,
        scored: rF2VehicleScoring,
        scoring: rF2Scoring,
    ) -> dict[str, float | int | bool | None]:
        info = scoring.mScoringInfo
        velocity = car.mLocalVel
        speed = math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2)
        yaw, pitch, roll = _orientation_angles(car)

        values: dict[str, float | int | bool | None] = {
            "time": car.mElapsedTime,
            "distance": scored.mLapDist,
            "lap": car.mLapNumber,
            "lap_time": car.mElapsedTime - car.mLapStartET,
            "speed": speed,
            "rpm": car.mEngineRPM,
            "gear": car.mGear,
            "throttle": car.mFilteredThrottle,
            "brake": car.mFilteredBrake,
            "clutch": car.mFilteredClutch,
            "steering": car.mFilteredSteering,
            "pos_x": car.mPos.x,
            "pos_y": car.mPos.y,
            "pos_z": car.mPos.z,
            "yaw": yaw,
            "pitch": pitch,
            "roll": roll,
            "accel_lat": car.mLocalAccel.x,
            "accel_vert": car.mLocalAccel.y,
            "accel_long": car.mLocalAccel.z,
            "fuel_level": car.mFuel,
            "fuel_used_lap": self._fuel_used_this_lap(car.mLapNumber, car.mFuel),
            "water_temp": _celsius_to_kelvin(car.mEngineWaterTemp),
            "oil_temp": _celsius_to_kelvin(car.mEngineOilTemp),
            "air_temp": _celsius_to_kelvin(info.mAmbientTemp),
            "track_temp": _celsius_to_kelvin(info.mTrackTemp),
            "rain_pct": info.mRaining,
            "wind_speed": math.sqrt(info.mWind.x**2 + info.mWind.y**2 + info.mWind.z**2),
            "wind_dir": math.atan2(info.mWind.x, info.mWind.z),
            # rF2 exposes no DRS/ERS/ABS/TC flags in this buffer. Absent, not
            # guessed — the UI shows them as unavailable.
            "drs": None,
            "ers_deploy": None,
            "ers_store": None,
            "abs_active": None,
            "tc_active": None,
        }

        for index, corner in enumerate(CORNERS):
            wheel = car.mWheels[index]
            for band_index, band in enumerate(BANDS):
                values[f"tyre_temp_{corner}_{band}"] = wheel.mTemperature[band_index]
            values[f"tyre_press_{corner}"] = wheel.mPressure
            # rF2 reports 1.0 for a new tyre; the schema defines 0 as new.
            values[f"tyre_wear_{corner}"] = 1.0 - wheel.mWear
            values[f"brake_temp_{corner}"] = wheel.mBrakeTemp
            values[f"brake_pressure_{corner}"] = wheel.mBrakePressure
            values[f"susp_travel_{corner}"] = wheel.mSuspensionDeflection
            values[f"ride_height_{corner}"] = wheel.mRideHeight

        for index, severity in enumerate(("front", "rear", "left", "right")):
            values[f"damage_{severity}"] = car.mDentSeverity[index] / 2.0

        values["damage_engine"] = None
        values["damage_gearbox"] = None

        return values


def _mapped_keys() -> frozenset[str]:
    keys = {
        "time", "distance", "lap", "lap_time", "speed", "rpm", "gear",
        "throttle", "brake", "clutch", "steering",
        "pos_x", "pos_y", "pos_z", "yaw", "pitch", "roll",
        "accel_lat", "accel_long", "accel_vert",
        "fuel_level", "fuel_used_lap",
        "water_temp", "oil_temp", "air_temp", "track_temp",
        "rain_pct", "wind_speed", "wind_dir",
        "damage_front", "damage_rear", "damage_left", "damage_right",
    }  # fmt: skip
    for corner in CORNERS:
        keys.update(
            {
                f"tyre_press_{corner}",
                f"tyre_wear_{corner}",
                f"brake_temp_{corner}",
                f"brake_pressure_{corner}",
                f"susp_travel_{corner}",
                f"ride_height_{corner}",
            }
        )
        keys.update(f"tyre_temp_{corner}_{band}" for band in BANDS)
    return frozenset(keys)


_MAPPED_KEYS = _mapped_keys()
