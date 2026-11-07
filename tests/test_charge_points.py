"""Check charge point identity, discovery, and state interpretation."""

from datetime import datetime, timezone

from aioresponses import aioresponses
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.helpers import entity_registry as er

URL = "https://api.emp.emob-enbw.com/emobility-public-api/api/v1/chargestations/2137426"
POINT_A = {
    "evseId": "DE*WLN*EP001941",
    "status": "AVAILABLE",
    "state": {"updatedAt": 1793582589645, "value": "AVAILABLE"},
    "connectors": [{"plugTypeName": "Typ 2", "maxPowerInKw": 22, "cableAttached": False}],
}
POINT_B = {
    "evseId": "DE*WLN*EP001942",
    "status": "OCCUPIED",
    "state": {"updatedAt": 1793685143813, "value": "OCCUPIED"},
    "connectors": [{"plugTypeName": "Typ 2", "maxPowerInKw": 22, "cableAttached": False}],
}
PAYLOAD = {
    "stationId": 2137426,
    "shortAddress": "Quettinger Str. 106, 51381 Leverkusen, DE",
    "operator": "Wirelane GmbH",
    "lat": 51.06225,
    "lon": 7.032111,
    "numberOfChargePoints": 1,
    "availableChargePoints": 1,
    "openingTimes": {"twentyFourSeven": True},
    "chargePoints": [POINT_A],
}


def _entry(hass):
    entry = MockConfigEntry(
        domain="charge_station_map",
        title="Test Station",
        data={"station_number": "2137426", "api_key": "dummy", "name": "Test Station"},
        unique_id="2137426",
    )
    entry.add_to_hass(hass)
    return entry


@pytest.mark.asyncio
async def test_new_point_appears_and_reordering_keeps_identity(hass):
    """Later API updates may add and reorder EVSE IDs."""
    entry = _entry(hass)
    updated = {
        **PAYLOAD,
        "numberOfChargePoints": 2,
        "availableChargePoints": 1,
        "chargePoints": [POINT_B, POINT_A],
    }
    with aioresponses() as responses:
        responses.get(URL, payload=PAYLOAD)
        responses.get(URL, payload=updated, repeat=True)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        registry = er.async_get(hass)
        status_a = registry.async_get_entity_id(
            "sensor",
            "charge_station_map",
            "charge_station_map_station_2137426_charge_point_status_DE*WLN*EP001941",
        )
        assert status_a is not None

        await entry.runtime_data.async_refresh()
        await hass.async_block_till_done()

    status_b = registry.async_get_entity_id(
        "sensor",
        "charge_station_map",
        "charge_station_map_station_2137426_charge_point_status_DE*WLN*EP001942",
    )
    assert status_b is not None
    assert status_b != status_a
    assert hass.states.get(status_a).attributes["evseId"] == POINT_A["evseId"]
    assert hass.states.get(status_b).attributes["evseId"] == POINT_B["evseId"]
    assert hass.states.get(status_a).state == "AVAILABLE"
    assert hass.states.get(status_b).state == "OCCUPIED"
    updated_at = hass.states.get(status_b).attributes["updatedAt"]
    if isinstance(updated_at, str):
        updated_at = datetime.fromisoformat(updated_at)
    assert updated_at == datetime.fromtimestamp(1793685143813 / 1000, tz=timezone.utc)
    available = hass.states.get("sensor.test_station_available_charge_points")
    assert available.attributes["latitude"] == 51.06225
    assert available.attributes["longitude"] == 7.032111


@pytest.mark.parametrize(
    "old_unique_id",
    [
        "charge_station_map_station_2137426_charge_point_1",
        "charge_station_map_station_2137426_charge_point_DE*WLN*EP001941",
    ],
)
@pytest.mark.asyncio
async def test_legacy_binary_point_is_removed(hass, old_unique_id):
    """Old duplicate point entities are removed when the single status sensor loads."""
    registry = er.async_get(hass)
    legacy = registry.async_get_or_create(
        "binary_sensor",
        "charge_station_map",
        old_unique_id,
        suggested_object_id="saved_charge_point",
    )
    entry = _entry(hass)
    with aioresponses() as responses:
        responses.get(URL, payload=PAYLOAD, repeat=True)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert registry.async_get(legacy.entity_id) is None
    assert hass.states.get(legacy.entity_id) is None
    assert hass.states.get("sensor.test_station_charge_point_1_22_kw_status").state == "AVAILABLE"


@pytest.mark.parametrize(
    "status",
    [
        "AVAILABLE",
        "OCCUPIED",
        "RESERVED",
        "BLOCKED",
        "OUT_OF_SERVICE",
        "UNKNOWN",
        "CHARGING",
    ],
)
@pytest.mark.asyncio
async def test_charge_point_status_states(hass, status):
    """The only point entity preserves every API state without a binary duplicate."""
    payload = {**PAYLOAD, "chargePoints": [{**POINT_A, "status": status}]}
    entry = _entry(hass)
    with aioresponses() as responses:
        responses.get(URL, payload=payload, repeat=True)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    status_sensor = hass.states.get("sensor.test_station_charge_point_1_22_kw_status")
    assert status_sensor.state == status
    assert status in status_sensor.attributes["options"]
    assert status_sensor.attributes["connectors"] == [
        {
            "plugType": "Typ 2",
            "plugTypeName": "Typ 2",
            "maxPowerInKw": 22,
            "cableAttached": False,
        }
    ]
    assert not any(
        state.entity_id.startswith("binary_sensor.") and state.attributes.get("evseId")
        for state in hass.states.async_all()
    )


@pytest.mark.asyncio
async def test_status_falls_back_to_state_value(hass):
    """Use the nested API state when a charge point has no top-level status."""
    point = {key: value for key, value in POINT_A.items() if key != "status"}
    point["state"] = {"value": "OCCUPIED", "updatedAt": 1793582589645}
    entry = _entry(hass)
    with aioresponses() as responses:
        responses.get(URL, payload={**PAYLOAD, "chargePoints": [point]}, repeat=True)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.test_station_charge_point_1_22_kw_status").state == "OCCUPIED"
