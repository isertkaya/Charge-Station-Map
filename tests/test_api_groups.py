"""The EnBW search API can return groups even with grouping disabled."""

from urllib.parse import parse_qs, urlsplit

import pytest

from custom_components.charge_station_map.api import EnbwApiClient, EnbwApiError


def _group(from_lat, from_lon, to_lat, to_lon):
    return {
        "grouped": True,
        "viewPort": {
            "lowerLeftLat": from_lat,
            "lowerLeftLon": from_lon,
            "upperRightLat": to_lat,
            "upperRightLon": to_lon,
        },
    }


@pytest.mark.asyncio
async def test_search_expands_nested_groups_and_deduplicates(monkeypatch):
    client = EnbwApiClient(None, "dummy")
    requested = []

    async def get(url):
        params = parse_qs(urlsplit(url).query)
        bounds = tuple(
            float(params[key][0])
            for key in ("fromLat", "fromLon", "toLat", "toLon")
        )
        requested.append(bounds)
        if bounds == (0.0, 0.0, 4.0, 4.0):
            return [
                {"stationId": 1, "grouped": False},
                _group(1, 1, 3, 3),
            ]
        if bounds == (1.0, 1.0, 3.0, 3.0):
            return [
                {"stationId": 1, "grouped": False},
                _group(1.5, 1.5, 2.5, 2.5),
            ]
        if bounds == (1.5, 1.5, 2.5, 2.5):
            return [{"stationId": 2, "grouped": False}]
        raise AssertionError(f"Unexpected bounds: {bounds}")

    monkeypatch.setattr(client, "_get", get)
    stations = await client.async_get_charge_stations(0, 0, 4, 4)

    assert {station["stationId"] for station in stations} == {1, 2}
    assert requested == [
        (0.0, 0.0, 4.0, 4.0),
        (1.0, 1.0, 3.0, 3.0),
        (1.5, 1.5, 2.5, 2.5),
    ]


@pytest.mark.asyncio
async def test_unresolvable_group_is_not_silently_dropped(monkeypatch):
    client = EnbwApiClient(None, "dummy")

    async def get(url):
        return [{"grouped": True}]

    monkeypatch.setattr(client, "_get", get)
    with pytest.raises(EnbwApiError, match="viewport"):
        await client.async_get_charge_stations(0, 0, 4, 4)
