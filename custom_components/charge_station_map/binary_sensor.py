"""Binary sensor platform for the EnBW charge stations integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_registry as er

from .const import (
    ATTR_ADDRESS,
    ATTR_ALWAYS_OPEN,
    ATTR_AVAILABLE_CHARGE_POINTS,
    ATTR_CABLE_ATTACHED,
    ATTR_CLOSED_ON_HOLIDAYS,
    ATTR_MAX_POWER_IN_KW,
    ATTR_MAX_POWER_PER_PLUG_TYPE_IN_KW,
    ATTR_NEXT_CLOSING_TIME,
    ATTR_NEXT_OPENING_TIME,
    ATTR_OPENING_HOURS,
    ATTR_OPERATOR,
    ATTR_PLUG_TYPE_NAME,
    ATTR_STATION_ID,
    ATTR_TOTAL_CHARGE_POINTS,
    ATTR_UPDATED_AT,
    DOMAIN,
)
from .coordinator import EnbwConfigEntry, EnbwDataUpdateCoordinator
from .entity import EnbwEntity
from .payload import station_updated_at

PARALLEL_UPDATES = 0


def _station_is_open(data: dict[str, Any]) -> bool | None:
    """Return whether the station is currently open, if known."""
    opening_times = data.get("openingTimes") or {}
    if opening_times.get("twentyFourSeven") or data.get("alwaysOpen") is True:
        return True
    if opening_times.get("nextClosingTime"):
        return True
    if opening_times.get("nextOpeningTime"):
        return False
    return None


@dataclass(frozen=True, kw_only=True)
class EnbwBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes an EnBW diagnostic binary sensor entity."""

    is_on_fn: Callable[[dict[str, Any]], bool | None]


DIAGNOSTIC_BINARY_SENSORS: tuple[EnbwBinarySensorEntityDescription, ...] = (
    EnbwBinarySensorEntityDescription(
        key="always_open",
        translation_key="always_open",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data: (data.get("openingTimes") or {}).get(
            "twentyFourSeven"
        ),
    ),
    EnbwBinarySensorEntityDescription(
        key="closed_on_holidays",
        translation_key="closed_on_holidays",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data: (data.get("openingTimes") or {}).get(
            "closedOnHolidays"
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: EnbwConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the EnBW binary sensors from a config entry."""
    coordinator = config_entry.runtime_data

    entities: list[BinarySensorEntity] = [
        ChargeStationStateBinarySensor(coordinator),
        StationOpenBinarySensor(coordinator),
    ]
    entities.extend(
        EnbwDiagnosticBinarySensor(coordinator, description)
        for description in DIAGNOSTIC_BINARY_SENSORS
    )

    registry = er.async_get(hass)
    old_point_prefix = f"{DOMAIN}_station_{coordinator.station_number}_charge_point_"
    for registered in tuple(registry.entities.values()):
        if (
            registered.platform == DOMAIN
            and registered.entity_id.startswith("binary_sensor.")
            and registered.unique_id.startswith(old_point_prefix)
        ):
            registry.async_remove(registered.entity_id)
    async_add_entities(entities)


class ChargeStationStateBinarySensor(EnbwEntity, BinarySensorEntity):
    """Binary sensor reporting whether the station has free charge points."""

    _attr_translation_key = "charge_station"

    def __init__(self, coordinator: EnbwDataUpdateCoordinator) -> None:
        """Initialize the station state binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"charge_station_map_station_{coordinator.station_number}_state"

    @property
    def is_on(self) -> bool | None:
        """Return True if at least one charge point is free and reachable."""
        data = self.coordinator.data
        if data is None:
            return None
        available_count = data.get("availableChargePoints")
        if not isinstance(available_count, (int, float)):
            return None
        if available_count <= 0:
            return False
        return _station_is_open(data) is not False

    @property
    def icon(self) -> str:
        """Return the icon for the entity."""
        return "mdi:car-electric-outline" if self.is_on else "mdi:car-electric"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra attributes describing the station."""
        data = self.coordinator.data
        if data is None:
            return None

        connectors = [
            connector
            for point in data.get("chargePoints", [])
            for connector in (point.get("connectors") or [])
        ]
        by_type: dict[str, list[dict[str, Any]]] = {}
        for connector in connectors:
            plug_type = connector.get("plugTypeName") or connector.get(
                "chargePlugTypeGroup"
            )
            if plug_type:
                by_type.setdefault(plug_type, []).append(connector)
        plug_type_cable_attached = {
            plug_type: any(c.get("cableAttached") for c in group)
            for plug_type, group in by_type.items()
        }
        plug_type_power = {
            plug_type: max(
                (c["maxPowerInKw"] for c in group if c.get("maxPowerInKw") is not None),
                default=None,
            )
            for plug_type, group in by_type.items()
        }

        return {
            ATTR_CABLE_ATTACHED: plug_type_cable_attached,
            ATTR_PLUG_TYPE_NAME: list(by_type),
            ATTR_MAX_POWER_IN_KW: data.get("maxPowerInKw"),
            ATTR_MAX_POWER_PER_PLUG_TYPE_IN_KW: plug_type_power,
            ATTR_STATION_ID: str(data.get("stationId")),
            ATTR_ADDRESS: data.get("shortAddress"),
            ATTR_OPERATOR: data.get("operator"),
            ATTR_AVAILABLE_CHARGE_POINTS: data.get("availableChargePoints"),
            ATTR_TOTAL_CHARGE_POINTS: data.get("numberOfChargePoints"),
            ATTR_UPDATED_AT: station_updated_at(data),
        }


class StationOpenBinarySensor(EnbwEntity, BinarySensorEntity):
    """Binary sensor reporting whether the station is currently open."""

    _attr_translation_key = "station_open"

    def __init__(self, coordinator: EnbwDataUpdateCoordinator) -> None:
        """Initialize the station open binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"charge_station_map_station_{coordinator.station_number}_open"

    @property
    def is_on(self) -> bool | None:
        """Return True if the station is currently open."""
        data = self.coordinator.data
        if data is None:
            return None
        return _station_is_open(data)

    @property
    def icon(self) -> str:
        """Return the icon for the entity."""
        return "mdi:door-open" if self.is_on else "mdi:door-closed"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the opening hours details for this station."""
        data = self.coordinator.data
        if data is None:
            return None
        opening_times = data.get("openingTimes") or {}
        return {
            ATTR_ALWAYS_OPEN: data.get("alwaysOpen"),
            ATTR_OPENING_HOURS: data.get("openingHours"),
            ATTR_CLOSED_ON_HOLIDAYS: opening_times.get("closedOnHolidays"),
            ATTR_NEXT_OPENING_TIME: opening_times.get("nextOpeningTime"),
            ATTR_NEXT_CLOSING_TIME: opening_times.get("nextClosingTime"),
            ATTR_STATION_ID: str(data.get("stationId")),
        }


class EnbwDiagnosticBinarySensor(EnbwEntity, BinarySensorEntity):
    """Representation of a diagnostic EnBW binary sensor described declaratively."""

    entity_description: EnbwBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: EnbwDataUpdateCoordinator,
        description: EnbwBinarySensorEntityDescription,
    ) -> None:
        """Initialize the diagnostic binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = (
            f"charge_station_map_station_{coordinator.station_number}_{description.key}"
        )

    @property
    def is_on(self) -> bool | None:
        """Return the value of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.is_on_fn(self.coordinator.data)
