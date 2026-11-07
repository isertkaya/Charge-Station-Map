"""Sensor platform for the EnBW charge stations integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_ADDRESS,
    ATTR_CABLE_ATTACHED,
    ATTR_CONNECTORS,
    ATTR_EVSE_ID,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_MAX_POWER_IN_KW,
    ATTR_OUT_OF_SERVICE,
    ATTR_PLUG_TYPE_NAME,
    ATTR_STATE,
    ATTR_STATION_ID,
    ATTR_UPDATED_AT,
)
from .charge_points import charge_point_status, find_charge_point, iter_charge_points
from .coordinator import EnbwConfigEntry, EnbwDataUpdateCoordinator
from .entity import EnbwEntity
from .payload import point_updated_at, station_updated_at

PARALLEL_UPDATES = 0
KNOWN_CHARGE_POINT_STATUSES = (
    "AVAILABLE",
    "OCCUPIED",
    "RESERVED",
    "BLOCKED",
    "OUT_OF_SERVICE",
    "UNKNOWN",
)


@dataclass(frozen=True, kw_only=True)
class EnbwSensorEntityDescription(SensorEntityDescription):
    """Describes an EnBW sensor entity."""

    value_fn: Callable[[dict[str, Any]], int | str | datetime | None]


def _station_id(data: dict[str, Any]) -> str | None:
    """Return the station id as a string, if the payload carries one."""
    station_id = data.get("stationId")
    return None if station_id is None else str(station_id)


def _opening_hours(data: dict[str, Any]) -> str | None:
    """Return a human readable description of the opening hours."""
    opening_times = data.get("openingTimes") or {}
    if opening_times.get("twentyFourSeven"):
        return "24/7"
    return _compress_opening_hours(data.get("openingHours"))


_DAYS = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")
_DAY_PATTERN = re.compile(r"(?<![A-Za-z])(Mo|Di|Mi|Do|Fr|Sa|So):\s*")


def _compress_opening_hours(value: str | None) -> str | None:
    """Merge consecutive days with identical hours, e.g. "Mo-Fr: 08:00 - 20:00"."""
    if not value:
        return value
    parts = _DAY_PATTERN.split(value)
    # parts: [prefix, day, hours, day, hours, ...]
    if parts[0].strip() or len(parts) < 3:
        return value
    entries = [(parts[i], parts[i + 1].strip()) for i in range(1, len(parts), 2)]
    if any(not hours for _, hours in entries):
        return value

    groups: list[list[Any]] = []  # [first_day, last_day, hours]
    for day, hours in entries:
        if (
            groups
            and groups[-1][2] == hours
            and _DAYS.index(day) == _DAYS.index(groups[-1][1]) + 1
        ):
            groups[-1][1] = day
        else:
            groups.append([day, day, hours])

    def label(first: str, last: str) -> str:
        if first == last:
            return first
        return f"{first}-{last}"

    return ", ".join(f"{label(f, l)}: {h}" for f, l, h in groups)


def _next_opening_time(data: dict[str, Any]) -> datetime | None:
    """Return when the station next opens, if it is currently closed."""
    opening_times = data.get("openingTimes") or {}
    value = opening_times.get("nextOpeningTime")
    return dt_util.parse_datetime(value) if value else None


def _next_closing_time(data: dict[str, Any]) -> datetime | None:
    """Return when the station next closes, if it is currently open."""
    opening_times = data.get("openingTimes") or {}
    value = opening_times.get("nextClosingTime")
    return dt_util.parse_datetime(value) if value else None


SENSORS: tuple[EnbwSensorEntityDescription, ...] = (
    EnbwSensorEntityDescription(
        key="operator",
        translation_key="operator",
        value_fn=lambda data: data.get("operator"),
    ),
    EnbwSensorEntityDescription(
        key="station_number",
        translation_key="station_number",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_station_id,
    ),
    EnbwSensorEntityDescription(
        key="total_charge_points",
        translation_key="total_charge_points",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("numberOfChargePoints"),
    ),
    EnbwSensorEntityDescription(
        key="available_charge_points",
        translation_key="available_charge_points",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("availableChargePoints"),
    ),
    EnbwSensorEntityDescription(
        key="unknown_state_charge_points",
        translation_key="unknown_state_charge_points",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("unknownStateChargePoints"),
    ),
    EnbwSensorEntityDescription(
        key="opening_hours",
        translation_key="opening_hours",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_opening_hours,
    ),
    EnbwSensorEntityDescription(
        key="next_opening_time",
        translation_key="next_opening_time",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_next_opening_time,
    ),
    EnbwSensorEntityDescription(
        key="next_closing_time",
        translation_key="next_closing_time",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_next_closing_time,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: EnbwConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the EnBW sensors from a config entry."""
    coordinator = config_entry.runtime_data
    entities: list[SensorEntity] = [
        EnbwSensor(coordinator, description) for description in SENSORS
    ]
    known_points: set[str] = set()

    def add_new_points() -> list[ChargePointStatusSensor]:
        """Create a status sensor for each newly discovered EVSE ID."""
        new_entities = []
        for point_id, index, power in iter_charge_points(coordinator.data):
            if point_id in known_points:
                continue
            known_points.add(point_id)
            new_entities.append(
                ChargePointStatusSensor(coordinator, point_id, index, power)
            )
        return new_entities

    entities.extend(add_new_points())
    async_add_entities(entities)

    def on_update() -> None:
        if new_entities := add_new_points():
            async_add_entities(new_entities)

    config_entry.async_on_unload(coordinator.async_add_listener(on_update))


class ChargePointStatusSensor(EnbwEntity, SensorEntity):
    """Expose the exact API status of a charge point."""

    _attr_translation_key = "charge_point_status"
    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(
        self,
        coordinator: EnbwDataUpdateCoordinator,
        point_id: str,
        index: int,
        max_power_in_kw: int | float,
    ) -> None:
        """Initialize the charge point status sensor."""
        super().__init__(coordinator)
        self._point_id = point_id
        self._attr_translation_placeholders = {
            "index": str(index),
            "power": f"{max_power_in_kw:g}",
        }
        self._attr_unique_id = (
            f"charge_station_map_station_{coordinator.station_number}"
            f"_charge_point_status_{point_id}"
        )

    def _point(self) -> dict[str, Any] | None:
        """Return this EVSE in the current response."""
        return find_charge_point(self.coordinator.data, self._point_id)

    @property
    def available(self) -> bool:
        """Return whether this EVSE is still present in the API response."""
        return super().available and self._point() is not None

    @property
    def options(self) -> list[str]:
        """Include an unexpected API status without hiding its original value."""
        status = self.native_value
        if status and status not in KNOWN_CHARGE_POINT_STATUSES:
            return [*KNOWN_CHARGE_POINT_STATUSES, status]
        return list(KNOWN_CHARGE_POINT_STATUSES)

    @property
    def native_value(self) -> str | None:
        """Return the unmodified status code for automations and translations."""
        point = self._point()
        return charge_point_status(point) if point is not None else None

    @property
    def icon(self) -> str:
        """Choose an icon from the current state and connector type."""
        point = self._point()
        if point is None:
            return "mdi:car-electric"
        status = charge_point_status(point)
        if status == "OCCUPIED":
            return "mdi:car-electric-outline"
        if status == "OUT_OF_SERVICE":
            return "mdi:alert-circle-outline"
        connectors = point.get("connectors") or []
        if len(connectors) != 1:
            return "mdi:car-electric"
        connector = connectors[0]
        plug_type_name = connector.get("plugTypeName") or ""
        if plug_type_name == "CHAdeMO":
            return "mdi:ev-plug-chademo"
        if "tesla" in plug_type_name.lower():
            return "mdi:ev-plug-tesla"
        max_power = connector.get("maxPowerInKw")
        if isinstance(max_power, (int, float)) and max_power > 22:
            return "mdi:ev-plug-ccs2"
        return "mdi:ev-plug-type2"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose the status, original timestamp, and connector details together."""
        point = self._point()
        data = self.coordinator.data
        if point is None or data is None:
            return None
        connectors = point.get("connectors") or []
        status = charge_point_status(point)
        return {
            ATTR_CABLE_ATTACHED: [c.get("cableAttached") for c in connectors],
            ATTR_PLUG_TYPE_NAME: [c.get("plugTypeName") for c in connectors],
            ATTR_MAX_POWER_IN_KW: [c.get("maxPowerInKw") for c in connectors],
            ATTR_CONNECTORS: [
                {
                    "plugType": c.get("chargePlugTypeGroup") or c.get("plugTypeName"),
                    "plugTypeName": c.get("plugTypeName"),
                    "maxPowerInKw": c.get("maxPowerInKw"),
                    "cableAttached": c.get("cableAttached"),
                }
                for c in connectors
            ],
            ATTR_ADDRESS: data.get("shortAddress"),
            ATTR_EVSE_ID: self._point_id,
            ATTR_STATE: status,
            ATTR_STATION_ID: str(data.get("stationId")),
            ATTR_UPDATED_AT: point_updated_at(point),
            ATTR_OUT_OF_SERVICE: status == "OUT_OF_SERVICE",
        }


class EnbwSensor(EnbwEntity, SensorEntity):
    """Representation of an EnBW charge station sensor."""

    entity_description: EnbwSensorEntityDescription

    def __init__(
        self,
        coordinator: EnbwDataUpdateCoordinator,
        description: EnbwSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = (
            f"charge_station_map_station_{coordinator.station_number}_{description.key}"
        )

    @property
    def native_value(self) -> int | str | datetime | None:
        """Return the value of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return location info on the available charge points sensor."""
        if self.entity_description.key != "available_charge_points":
            return None
        data = self.coordinator.data
        if data is None:
            return None
        return {
            ATTR_LATITUDE: data.get("lat"),
            ATTR_LONGITUDE: data.get("lon"),
            ATTR_UPDATED_AT: station_updated_at(data),
        }
