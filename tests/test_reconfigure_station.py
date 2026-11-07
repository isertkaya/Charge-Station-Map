"""Changing a configured station keeps its device and prevents duplicates."""

from aioresponses import aioresponses
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.helpers import device_registry as dr, entity_registry as er

BASE = "https://api.emp.emob-enbw.com/emobility-public-api/api/v1/chargestations"


def _payload(station_id):
    return {
        "stationId": station_id,
        "shortAddress": f"Station {station_id}",
        "lat": 51.0,
        "lon": 7.0,
        "numberOfChargePoints": 1,
        "availableChargePoints": 1,
        "openingTimes": {"twentyFourSeven": True},
        "chargePoints": [
            {
                "evseId": f"DE*TEST*E{station_id}",
                "status": "AVAILABLE",
                "connectors": [{"plugTypeName": "Typ 2", "maxPowerInKw": 22}],
            }
        ],
    }


@pytest.mark.asyncio
async def test_station_change_migrates_registry_and_device(hass):
    entry = MockConfigEntry(
        domain="charge_station_map",
        title="Old station",
        data={"station_number": "222", "api_key": "dummy", "name": "Old station"},
        unique_id="222",
    )
    entry.add_to_hass(hass)
    with aioresponses() as responses:
        responses.get(f"{BASE}/222", payload=_payload(222), repeat=True)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    registry = er.async_get(hass)
    old_unique = "charge_station_map_station_222_state"
    state_entity_id = registry.async_get_entity_id(
        "binary_sensor", "charge_station_map", old_unique
    )
    devices = dr.async_get(hass)
    old_device = devices.async_get_device(
        identifiers={("charge_station_map", "charge_station_map_station_222")}
    )
    assert state_entity_id and old_device

    with aioresponses() as responses:
        responses.get(f"{BASE}/333", payload=_payload(333), repeat=True)
        result = await hass.config_entries.flow.async_init(
            "charge_station_map",
            context={"source": "reconfigure", "entry_id": entry.entry_id},
        )
        assert result["step_id"] == "reconfigure"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"station_number": "333", "api_key": "dummy", "name": "New station"},
        )
        await hass.async_block_till_done()

    assert result["type"].value == "abort"
    assert entry.unique_id == "333"
    assert "previous_station_number" not in entry.data
    assert registry.async_get_entity_id("binary_sensor", "charge_station_map", old_unique) is None
    assert registry.async_get_entity_id(
        "binary_sensor", "charge_station_map", "charge_station_map_station_333_state"
    ) == state_entity_id
    new_device = devices.async_get_device(
        identifiers={("charge_station_map", "charge_station_map_station_333")}
    )
    assert new_device and new_device.id == old_device.id
    assert registry.async_get_entity_id(
        "binary_sensor",
        "charge_station_map",
        "charge_station_map_station_222_charge_point_DE*TEST*E222",
    ) is None
    assert registry.async_get_entity_id(
        "sensor",
        "charge_station_map",
        "charge_station_map_station_222_charge_point_status_DE*TEST*E222",
    ) is None


@pytest.mark.asyncio
async def test_station_change_rejects_existing_station(hass):
    for number in (222, 333):
        MockConfigEntry(
            domain="charge_station_map",
            title=f"Station {number}",
            data={"station_number": str(number), "api_key": "dummy", "name": "Test"},
            unique_id=str(number),
        ).add_to_hass(hass)
    first = next(
        entry
        for entry in hass.config_entries.async_entries("charge_station_map")
        if entry.unique_id == "222"
    )
    result = await hass.config_entries.flow.async_init(
        "charge_station_map",
        context={"source": "reconfigure", "entry_id": first.entry_id},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"station_number": "333", "api_key": "dummy", "name": "Duplicate"},
    )
    assert result["step_id"] == "reconfigure"
    assert result["errors"]["base"] == "already_configured"
