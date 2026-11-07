"""Renewing a shared API key updates every station that used it."""

from aioresponses import aioresponses
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

BASE = "https://api.emp.emob-enbw.com/emobility-public-api/api/v1/chargestations"


@pytest.mark.asyncio
async def test_reauth_updates_entries_with_the_same_old_key(hass):
    entries = [
        MockConfigEntry(
            domain="charge_station_map",
            title=f"Station {station_id}",
            data={
                "station_number": str(station_id),
                "api_key": key,
                "name": f"Station {station_id}",
            },
            unique_id=str(station_id),
        )
        for station_id, key in ((111, "OLD"), (222, "OLD"), (333, "OTHER"))
    ]
    for entry in entries:
        entry.add_to_hass(hass)

    with aioresponses() as responses:
        for station_id in (111, 222):
            responses.get(
                f"{BASE}/{station_id}",
                payload={"stationId": station_id, "chargePoints": []},
                repeat=True,
            )
        result = await hass.config_entries.flow.async_init(
            "charge_station_map",
            context={"source": "reauth", "entry_id": entries[0].entry_id},
            data=entries[0].data,
        )
        assert result["step_id"] == "reauth_confirm"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"api_key": "NEW"}
        )
        await hass.async_block_till_done()

    assert result["type"].value == "abort"
    assert entries[0].data["api_key"] == "NEW"
    assert entries[1].data["api_key"] == "NEW"
    assert entries[2].data["api_key"] == "OTHER"
