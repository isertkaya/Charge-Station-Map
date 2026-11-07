"""Verify the station number is exposed as a sensor."""

from aioresponses import aioresponses
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

URL = "https://api.emp.emob-enbw.com/emobility-public-api/api/v1/chargestations/393894"

PAYLOAD = {
    "stationId": 393894,
    "shortAddress": "Teststr. 1",
    "operator": "Wirelane GmbH",
    "lat": 48.78,
    "lon": 9.18,
    "maxPowerInKw": 150,
    "numberOfChargePoints": 1,
    "availableChargePoints": 1,
    "unknownStateChargePoints": 0,
    "plugTypeNames": ["CCS (Typ 2)"],
    "chargePoints": [
        {
            "evseId": "DE*ENB*E393894001",
            "status": "AVAILABLE",
            "connectors": [
                {"plugTypeName": "CCS (Typ 2)", "cableAttached": True, "maxPowerInKw": 150}
            ],
        }
    ],
}

@pytest.mark.asyncio
async def test_station_number_sensor(hass):
    entry = MockConfigEntry(
        domain="charge_station_map",
        title="Test Station",
        data={"station_number": "393894", "api_key": "dummy", "name": "Test Station"},
        unique_id="393894",
    )
    entry.add_to_hass(hass)

    with aioresponses() as m:
        m.get(URL, payload=PAYLOAD, repeat=True)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.test_station_station_number")
    assert state is not None, [
        s.entity_id for s in hass.states.async_all() if s.entity_id.startswith("sensor.")
    ]
    assert state.state == "393894"
    assert hass.states.get("sensor.test_station_operator").state == "Wirelane GmbH"

    # Still present and correct after a reload.
    with aioresponses() as m:
        m.get(URL, payload=PAYLOAD, repeat=True)
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.test_station_station_number")
    assert state.state == "393894"

@pytest.mark.asyncio
async def test_station_number_sensor_missing_id(hass):
    """A payload without stationId must not crash the sensor."""
    payload = {**PAYLOAD}
    del payload["stationId"]

    entry = MockConfigEntry(
        domain="charge_station_map",
        title="No Id",
        data={"station_number": "393894", "api_key": "dummy", "name": "No Id"},
        unique_id="393894",
    )
    entry.add_to_hass(hass)

    with aioresponses() as m:
        m.get(URL, payload=payload, repeat=True)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.no_id_station_number")
    assert state.state == "unknown"


@pytest.mark.asyncio
async def test_connector_attributes_are_grouped_by_actual_plug_type(hass):
    payload = {
        **PAYLOAD,
        "plugTypeNames": ["Typ 2", "CCS"],
        "chargePoints": [
            {
                "evseId": "DE*ENB*E393894001",
                "status": "AVAILABLE",
                "connectors": [
                    {
                        "chargePlugTypeGroup": "TYPE_2",
                        "plugTypeName": "Typ 2",
                        "maxPowerInKw": 22,
                        "cableAttached": False,
                    },
                    {
                        "chargePlugTypeGroup": "CCS",
                        "plugTypeName": "CCS",
                        "maxPowerInKw": 150,
                        "cableAttached": True,
                    },
                ],
            }
        ],
    }
    entry = MockConfigEntry(
        domain="charge_station_map",
        title="Connector Test",
        data={"station_number": "393894", "api_key": "dummy", "name": "Connector Test"},
        unique_id="393894",
    )
    entry.add_to_hass(hass)
    with aioresponses() as responses:
        responses.get(URL, payload=payload, repeat=True)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    station = hass.states.get("binary_sensor.connector_test_availability")
    assert station.attributes["cableAttached"] == {"Typ 2": False, "CCS": True}
    assert station.attributes["maxPowerInKwPerPlugType"] == {
        "Typ 2": 22,
        "CCS": 150,
    }
    point = next(
        state
        for state in hass.states.async_all()
        if state.entity_id.startswith("sensor.")
        and state.attributes.get("evseId") == "DE*ENB*E393894001"
    )
    assert point.attributes["connectors"] == [
        {
            "plugType": "TYPE_2",
            "plugTypeName": "Typ 2",
            "maxPowerInKw": 22,
            "cableAttached": False,
        },
        {
            "plugType": "CCS",
            "plugTypeName": "CCS",
            "maxPowerInKw": 150,
            "cableAttached": True,
        },
    ]
