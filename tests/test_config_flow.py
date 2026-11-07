"""Test that the API key can be omitted once a station is already configured."""

import re

from aioresponses import aioresponses
import pytest
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

DOMAIN = "charge_station_map"
BASE = "https://api.emp.emob-enbw.com/emobility-public-api/api/v1/chargestations"
SEARCH_URL = re.compile(rf"^{re.escape(BASE)}\?.*")

USER_INPUT = {"location": {"latitude": 48.78, "longitude": 9.18, "radius": 10000}}

def payload(station_id):
    return {
        "stationId": station_id,
        "shortAddress": f"Teststr. {station_id}",
        "lat": 48.78,
        "lon": 9.18,
        "maxPowerInKw": 150,
        "numberOfChargePoints": 1,
        "availableChargePoints": 1,
        "unknownStateChargePoints": 0,
        "plugTypeNames": ["CCS (Typ 2)"],
        "chargePoints": [
            {
                "evseId": f"DE*ENB*E{station_id}001",
                "status": "AVAILABLE",
                "connectors": [
                    {
                        "plugTypeName": "CCS (Typ 2)",
                        "cableAttached": True,
                        "maxPowerInKw": 150,
                    }
                ],
            }
        ],
    }


async def _add_station(hass, station_id: int, user_input: dict):
    """Run the full flow: search area -> pick station -> entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with aioresponses() as m:
        m.get(SEARCH_URL, payload=[payload(station_id)], repeat=True)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input
        )
    assert result["step_id"] == "filter_stations", result
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["step_id"] == "search_station", result

    with aioresponses() as m:
        m.get(f"{BASE}/{station_id}", payload=payload(station_id), repeat=True)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"station_number": str(station_id)}
        )
        await hass.async_block_till_done()
    return result

@pytest.mark.asyncio
async def test_first_entry_requires_key_second_reuses_it(
    hass
):
    # --- First station: API key is required ---
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    api_key_marker = next(
        k for k in result["data_schema"].schema if str(k) == "api_key"
    )
    assert isinstance(api_key_marker, vol.Required)
    hass.config_entries.flow.async_abort(result["flow_id"])

    result = await _add_station(hass, 111111, {**USER_INPUT, "api_key": "SECRET-KEY"})
    assert result["type"] == FlowResultType.CREATE_ENTRY, result
    assert result["data"]["api_key"] == "SECRET-KEY"

    # --- Second station: the stored key is reused without showing the field ---
    result2 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert "api_key" not in [str(k) for k in result2["data_schema"].schema]
    hass.config_entries.flow.async_abort(result2["flow_id"])

    # Submit WITHOUT an api_key at all.
    result2 = await _add_station(hass, 222222, USER_INPUT)
    assert result2["type"] == FlowResultType.CREATE_ENTRY, result2
    assert result2["data"]["api_key"] == "SECRET-KEY", "should reuse the stored key"

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 2
    assert all(e.state is config_entries.ConfigEntryState.LOADED for e in entries)

@pytest.mark.asyncio
async def test_second_entry_uses_first_key(hass):
    """A second station continues to use the key from the first entry."""
    await _add_station(hass, 111111, {**USER_INPUT, "api_key": "FIRST-KEY"})
    result2 = await _add_station(hass, 222222, USER_INPUT)
    assert result2["data"]["api_key"] == "FIRST-KEY"


@pytest.mark.asyncio
async def test_expired_shared_key_can_be_replaced_during_new_setup(hass):
    """An expired stored key must not trap the user on a form with no key field."""
    MockConfigEntry(
        domain=DOMAIN,
        title="Existing station",
        data={"station_number": "111111", "api_key": "EXPIRED", "name": "Existing"},
        unique_id="111111",
    ).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert "api_key" not in [str(key) for key in result["data_schema"].schema]

    with aioresponses() as responses:
        responses.get(SEARCH_URL, status=401)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
    assert result["step_id"] == "user"
    assert result["errors"]["base"] == "invalid_auth"
    assert "api_key" in [str(key) for key in result["data_schema"].schema]

    with aioresponses() as responses:
        responses.get(SEARCH_URL, payload=[payload(222222)])
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**USER_INPUT, "api_key": "NEW"}
        )
    assert result["step_id"] == "filter_stations"
