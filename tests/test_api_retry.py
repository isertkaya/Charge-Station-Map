"""Transient HTTP failures should not make station lookups fail immediately."""

import aiohttp
from aioresponses import aioresponses
import pytest

from custom_components.charge_station_map.api import EnbwApiClient, EnbwAuthError

URL = "https://api.emp.emob-enbw.com/emobility-public-api/api/v1/chargestations/2137426"


@pytest.mark.asyncio
async def test_transient_http_failures_are_retried():
    with aioresponses() as responses:
        responses.get(URL, status=429, headers={"Retry-After": "0"})
        responses.get(URL, status=503)
        responses.get(URL, payload={"stationId": 2137426, "chargePoints": []})
        async with aiohttp.ClientSession() as session:
            result = await EnbwApiClient(session, "dummy").async_get_charge_station(
                "2137426"
            )

    assert result["stationId"] == 2137426
    assert len(responses.requests) == 1
    assert len(next(iter(responses.requests.values()))) == 3


@pytest.mark.asyncio
async def test_invalid_key_is_not_retried():
    with aioresponses() as responses:
        responses.get(URL, status=401)
        async with aiohttp.ClientSession() as session:
            with pytest.raises(EnbwAuthError):
                await EnbwApiClient(session, "dummy").async_get_charge_station(
                    "2137426"
                )

    assert len(next(iter(responses.requests.values()))) == 1
