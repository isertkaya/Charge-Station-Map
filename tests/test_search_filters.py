"""Search filters and picker labels use station summary fields."""

import re

from aioresponses import aioresponses
import pytest

BASE = "https://api.emp.emob-enbw.com/emobility-public-api/api/v1/chargestations"
SEARCH_URL = re.compile(rf"^{re.escape(BASE)}\?.*")


@pytest.mark.asyncio
async def test_filters_and_result_labels(hass):
    stations = [
        {
            "stationId": 1,
            "operator": "Other GmbH",
            "operatorCode": "DEOTH",
            "plugTypes": ["TYPE_2"],
            "plugTypeNames": ["Typ 2"],
            "maxPowerInKw": 22.0,
            "shortAddress": "Other Str. 1",
            "lat": 48.0,
            "lon": 9.0,
        },
        {
            "stationId": 2,
            "operator": "Wirelane GmbH",
            "operatorCode": "DEWLN",
            "plugTypes": ["TYPE_2"],
            "plugTypeNames": ["Typ 2"],
            "maxPowerInKw": 22.0,
            "shortAddress": "Quettinger Str. 106",
            "lat": 48.001,
            "lon": 9.0,
        },
        {
            "stationId": 3,
            "operator": "Wirelane GmbH",
            "operatorCode": "DEWLN",
            "plugTypes": ["CCS"],
            "plugTypeNames": ["CCS (Typ 2)"],
            "maxPowerInKw": 150.0,
            "shortAddress": "Fast Str. 2",
            "lat": 48.002,
            "lon": 9.0,
        },
    ]
    result = await hass.config_entries.flow.async_init(
        "charge_station_map", context={"source": "user"}
    )
    with aioresponses() as responses:
        responses.get(SEARCH_URL, payload=stations)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "api_key": "dummy",
                "location": {"latitude": 48.0, "longitude": 9.0, "radius": 10000},
            },
        )

    assert result["step_id"] == "filter_stations"
    schema = result["data_schema"].schema
    operator_selector = next(
        v for k, v in schema.items() if str(k) == "operator_filter"
    )
    plug_selector = next(
        v for k, v in schema.items() if str(k) == "plug_types_filter"
    )
    assert operator_selector.config["options"] == ["Other GmbH", "Wirelane GmbH"]
    assert operator_selector.config["multiple"] is True
    assert plug_selector.config["options"] == [
        {"value": "CCS", "label": "CCS (Typ 2) · CCS"},
        {"value": "TYPE_2", "label": "Typ 2 · TYPE_2"},
    ]
    assert plug_selector.config["multiple"] is True

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "operator_filter": ["Other GmbH", "Wirelane GmbH"],
            "plug_types_filter": ["TYPE_2"],
            "min_power_in_kw": 20,
        },
    )
    assert result["step_id"] == "search_station"
    selector = next(
        v
        for k, v in result["data_schema"].schema.items()
        if str(k) == "station_number"
    )
    assert [option["value"] for option in selector.config["options"]] == ["1", "2"]
    option = selector.config["options"][1]
    assert option["label"].startswith("Wirelane GmbH · 22 kW ·")
    assert option["label"].endswith("Quettinger Str. 106")


@pytest.mark.asyncio
async def test_minimum_power_filter(hass):
    result = await hass.config_entries.flow.async_init(
        "charge_station_map", context={"source": "user"}
    )
    stations = [
        {"stationId": 1, "lat": 48.0, "lon": 9.0, "maxPowerInKw": 22},
        {"stationId": 2, "lat": 48.001, "lon": 9.0, "maxPowerInKw": 150},
    ]
    with aioresponses() as responses:
        responses.get(SEARCH_URL, payload=stations)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "api_key": "dummy",
                "location": {"latitude": 48.0, "longitude": 9.0, "radius": 10000},
            },
        )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"min_power_in_kw": 100}
    )
    selector = next(
        v
        for k, v in result["data_schema"].schema.items()
        if str(k) == "station_number"
    )
    assert [o["value"] for o in selector.config["options"]] == ["2"]


@pytest.mark.asyncio
async def test_no_filter_match_stays_on_filter_form(hass):
    result = await hass.config_entries.flow.async_init(
        "charge_station_map", context={"source": "user"}
    )
    station = {
        "stationId": 1,
        "lat": 48.0,
        "lon": 9.0,
        "operator": "Wirelane GmbH",
        "plugTypes": ["TYPE_2"],
        "maxPowerInKw": 22,
    }
    with aioresponses() as responses:
        responses.get(SEARCH_URL, payload=[station])
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "api_key": "dummy",
                "location": {"latitude": 48.0, "longitude": 9.0, "radius": 10000},
            },
        )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"min_power_in_kw": 100}
    )
    assert result["step_id"] == "filter_stations"
    assert result["errors"] == {"base": "no_filter_matches"}
