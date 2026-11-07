"""The Charge Station Map integration."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import DOMAIN as LOVELACE_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
    entity_registry as er,
)

from .const import CARD_VERSION, DOMAIN, PREVIOUS_STATION_NUMBER, STATION_NUMBER
from .coordinator import EnbwConfigEntry, EnbwDataUpdateCoordinator
from .station import station_display_name

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.DEVICE_TRACKER,
    Platform.SENSOR,
]

CARD_URL = "/charge_station_map/charge-station-map-card.js"
_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def _async_register_card_resource(hass: HomeAssistant) -> None:
    """Make the dashboard cards available in the picker without manual setup."""
    lovelace = hass.data.get(LOVELACE_DOMAIN)
    if lovelace is None:
        _LOGGER.warning("Lovelace is unavailable; cannot register the dashboard cards")
        return
    if lovelace.resource_mode != "storage":
        _LOGGER.info(
            "Dashboard resources use YAML; add %s as a module in Lovelace YAML",
            CARD_URL,
        )
        return

    resources = lovelace.resources
    # Older Home Assistant versions load resource storage lazily. Reading the
    # collection before loading it can overwrite existing dashboard resources.
    await resources.async_get_info()
    card_url = f"{CARD_URL}?v={CARD_VERSION}"
    existing = next(
        (
            item
            for item in resources.async_items()
            if item.get("url", "").split("?", 1)[0] == CARD_URL
        ),
        None,
    )
    if existing is None:
        await resources.async_create_item({"res_type": "module", "url": card_url})
    elif existing.get("url") != card_url or existing.get("type") != "module":
        await resources.async_update_item(
            existing["id"], {"res_type": "module", "url": card_url}
        )


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Serve and register the dashboard cards."""
    card_file = Path(__file__).parent / "www" / "charge-station-map-card.js"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(card_file), cache_headers=False)]
    )
    await _async_register_card_resource(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: EnbwConfigEntry) -> bool:
    """Set up EnBW Charge Stations from a config entry."""
    coordinator = EnbwDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    if previous_station := entry.data.get(PREVIOUS_STATION_NUMBER):
        _migrate_station_number(hass, entry, previous_station)

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    def update_device_name() -> None:
        """Keep the device name aligned with current operator and address."""
        identifier = (DOMAIN, f"charge_station_map_station_{coordinator.station_number}")
        devices = dr.async_get(hass)
        device = devices.async_get_device(identifiers={identifier})
        if device is None or entry.entry_id not in device.config_entries:
            return
        name = station_display_name(coordinator.data or {}, coordinator.station_number)
        if device.name != name:
            devices.async_update_device(device.id, name=name)

    update_device_name()
    entry.async_on_unload(coordinator.async_add_listener(update_device_name))
    return True


def _migrate_station_number(
    hass: HomeAssistant, entry: EnbwConfigEntry, previous_station: str
) -> None:
    """Keep station entities and the device when a configured station changes."""
    current_station = entry.data[STATION_NUMBER]
    old_prefix = f"charge_station_map_station_{previous_station}_"
    new_prefix = f"charge_station_map_station_{current_station}_"
    registry = er.async_get(hass)
    for registered in er.async_entries_for_config_entry(registry, entry.entry_id):
        if not registered.unique_id.startswith(old_prefix):
            continue
        suffix = registered.unique_id[len(old_prefix) :]
        if suffix.startswith("charge_point_"):
            # The old EVSE belongs to the previous physical station.
            registry.async_remove(registered.entity_id)
            continue
        new_unique_id = new_prefix + suffix
        entity_domain = registered.entity_id.split(".", 1)[0]
        if not registry.async_get_entity_id(entity_domain, DOMAIN, new_unique_id):
            registry.async_update_entity(
                registered.entity_id, new_unique_id=new_unique_id
            )

    devices = dr.async_get(hass)
    old_identifier = (DOMAIN, f"charge_station_map_station_{previous_station}")
    device = devices.async_get_device(identifiers={old_identifier})
    if device and entry.entry_id in device.config_entries:
        devices.async_update_device(
            device.id,
            new_identifiers=(device.identifiers - {old_identifier})
            | {(DOMAIN, f"charge_station_map_station_{current_station}")},
        )

    hass.config_entries.async_update_entry(
        entry,
        data={
            key: value
            for key, value in entry.data.items()
            if key != PREVIOUS_STATION_NUMBER
        },
    )


async def async_unload_entry(hass: HomeAssistant, entry: EnbwConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_config_entry_device(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    device_entry: DeviceEntry,
) -> bool:
    """Remove a config entry from a device."""
    return True
