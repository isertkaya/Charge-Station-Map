"""The device name follows the operator and address from the API."""

from aioresponses import aioresponses
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.helpers import device_registry as dr
from custom_components.charge_station_map.station import station_display_name

URL = "https://api.emp.emob-enbw.com/emobility-public-api/api/v1/chargestations/2137426"
PAYLOAD = {
    "stationId": 2137426,
    "operator": "Wirelane GmbH",
    "shortAddress": "Quettinger Str. 106, Leverkusen",
    "lat": 51.06225,
    "lon": 7.032111,
    "numberOfChargePoints": 0,
    "availableChargePoints": 0,
    "chargePoints": [],
}


def test_name_uses_operator_code_when_name_is_missing():
    assert station_display_name(
        {"operatorCode": "DEWLN", "shortAddress": "Quettinger Str. 106"},
        "2137426",
    ) == "DEWLN · Quettinger Str. 106"


@pytest.mark.asyncio
async def test_existing_device_name_updates_with_operator_and_address(hass):
    """An old address-only config entry receives the new device name."""
    entry = MockConfigEntry(
        domain="charge_station_map",
        title="Quettinger Str. 106, Leverkusen",
        data={
            "station_number": "2137426",
            "api_key": "dummy",
            "name": "Quettinger Str. 106, Leverkusen",
        },
        unique_id="2137426",
    )
    entry.add_to_hass(hass)
    updated = {**PAYLOAD, "operator": "Neuer Betreiber", "shortAddress": "Neue Str. 2"}
    with aioresponses() as responses:
        responses.get(URL, payload=PAYLOAD)
        responses.get(URL, payload=updated, repeat=True)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        devices = dr.async_get(hass)
        device = devices.async_get_device(
            identifiers={
                ("charge_station_map", "charge_station_map_station_2137426")
            }
        )
        assert device is not None
        assert device.name == "Wirelane GmbH · Quettinger Str. 106, Leverkusen"

        await entry.runtime_data.async_refresh()
        await hass.async_block_till_done()

    device = devices.async_get(device.id)
    assert device.name == "Neuer Betreiber · Neue Str. 2"
