"""Async API client for the EnBW e-mobility public API."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

API_BASE = "https://api.emp.emob-enbw.com/emobility-public-api/api/v1"

DEFAULT_HEADERS = {
    "User-Agent": "Home Assistant",
    "Accept": "application/json",
    "Origin": "https://www.enbw.com",
    "Referer": "https://www.enbw.com/",
}

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=15)
RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})
MAX_ATTEMPTS = 3
MAX_GROUP_DEPTH = 6
MAX_GROUP_REQUESTS = 400
GROUP_REQUEST_CONCURRENCY = 8


class EnbwApiError(Exception):
    """Generic error talking to the EnBW API."""


class EnbwAuthError(EnbwApiError):
    """Raised when the API key is rejected (401/403)."""


class EnbwApiClient:
    """Thin async wrapper around the EnBW charge station endpoints."""

    def __init__(self, session: aiohttp.ClientSession, api_key: str) -> None:
        """Initialize the client."""
        self._session = session
        self._api_key = api_key

    def _headers(self) -> dict[str, str]:
        return {**DEFAULT_HEADERS, "Ocp-Apim-Subscription-Key": self._api_key}

    async def _get(self, url: str) -> Any:
        for attempt in range(MAX_ATTEMPTS):
            delay = 0.5 * 2**attempt
            try:
                async with self._session.get(
                    url, headers=self._headers(), timeout=DEFAULT_TIMEOUT
                ) as response:
                    if response.status in (401, 403):
                        raise EnbwAuthError(
                            f"API key rejected (HTTP {response.status})"
                        )
                    if response.status in RETRYABLE_STATUSES:
                        if attempt == MAX_ATTEMPTS - 1:
                            raise EnbwApiError(
                                f"Unexpected response (HTTP {response.status})"
                            )
                        retry_after = response.headers.get("Retry-After")
                        if retry_after:
                            try:
                                delay = min(max(float(retry_after), delay), 5)
                            except ValueError:
                                pass
                    elif response.status >= 400:
                        raise EnbwApiError(
                            f"Unexpected response (HTTP {response.status})"
                        )
                    else:
                        return await response.json()
            except (aiohttp.ClientError, TimeoutError, ValueError) as err:
                if attempt == MAX_ATTEMPTS - 1:
                    raise EnbwApiError(f"Error communicating with API: {err}") from err
            await asyncio.sleep(delay)

        raise EnbwApiError("Could not fetch charge station data")

    async def async_get_charge_station(self, station_number: str) -> dict[str, Any]:
        """Return the full detail payload for a single charge station."""
        data = await self._get(f"{API_BASE}/chargestations/{station_number}")
        if not isinstance(data, dict):
            raise EnbwApiError("Unexpected payload for charge station")
        return data

    async def async_get_charge_stations(
        self,
        from_lat: float,
        from_lon: float,
        to_lat: float,
        to_lon: float,
    ) -> list[dict[str, Any]]:
        """Return individual stations, expanding API groups as needed."""
        first_bounds = (from_lat, from_lon, to_lat, to_lon)
        pending = [(first_bounds, 0)]
        seen = {first_bounds}
        stations: dict[str, dict[str, Any]] = {}

        while pending:
            batch = pending[:GROUP_REQUEST_CONCURRENCY]
            del pending[:GROUP_REQUEST_CONCURRENCY]
            responses = await asyncio.gather(
                *(self._get_charge_stations_in_bounds(*bounds) for bounds, _ in batch)
            )
            for (bounds, depth), rows in zip(batch, responses, strict=True):
                for row in rows:
                    if row.get("grouped"):
                        if depth >= MAX_GROUP_DEPTH:
                            raise EnbwApiError("Charge station groups could not be resolved")
                        viewport = row.get("viewPort") or {}
                        try:
                            child_bounds = (
                                float(viewport["lowerLeftLat"]),
                                float(viewport["lowerLeftLon"]),
                                float(viewport["upperRightLat"]),
                                float(viewport["upperRightLon"]),
                            )
                        except (KeyError, TypeError, ValueError) as err:
                            raise EnbwApiError("Invalid charge station group viewport") from err
                        if child_bounds == bounds:
                            raise EnbwApiError("Charge station group did not narrow")
                        if child_bounds not in seen:
                            seen.add(child_bounds)
                            if len(seen) > MAX_GROUP_REQUESTS:
                                raise EnbwApiError("Too many charge station groups")
                            pending.append((child_bounds, depth + 1))
                    elif row.get("stationId") is not None:
                        stations[str(row["stationId"])] = row

        return list(stations.values())

    async def _get_charge_stations_in_bounds(
        self, from_lat: float, from_lon: float, to_lat: float, to_lon: float
    ) -> list[dict[str, Any]]:
        """Fetch one bounding box from the EnBW API."""
        url = (
            f"{API_BASE}/chargestations"
            f"?fromLat={from_lat}&toLat={to_lat}"
            f"&fromLon={from_lon}&toLon={to_lon}"
            "&grouping=false&groupingDivisor=15"
        )
        data = await self._get(url)
        if not isinstance(data, list):
            raise EnbwApiError("Unexpected payload for charge stations")
        return [x for x in data if isinstance(x, dict)]
