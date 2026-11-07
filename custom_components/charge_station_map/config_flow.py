"""Config flow for the EnBW Charge Stations integration."""

from __future__ import annotations

import logging
from math import cos, radians
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    LocationSelector,
    LocationSelectorConfig,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
from homeassistant.util.location import distance

from .api import EnbwApiClient, EnbwApiError, EnbwAuthError
from .const import (
    API_KEY,
    DEFAULT_SEARCH_RADIUS_M,
    DOMAIN,
    LOCATION,
    MIN_POWER_IN_KW,
    NAME,
    OPERATOR_FILTER,
    PLUG_TYPES_FILTER,
    PREVIOUS_STATION_NUMBER,
    STATION_NUMBER,
)
from .station import station_display_name

_LOGGER = logging.getLogger(__name__)


def _station_option(station: dict[str, Any], distance_m: float) -> SelectOptionDict:
    """Build a select option from a station payload."""
    operator = station.get("operator") or station.get("operatorCode") or "Unknown operator"
    power = station.get("maxPowerInKw")
    power_label = f"{power:g} kW" if isinstance(power, (int, float)) else "? kW"
    address = station.get("shortAddress") or f"Station {station['stationId']}"
    return SelectOptionDict(
        value=str(station["stationId"]),
        label=f"{operator} · {power_label} · {distance_m / 1000:.1f} km · {address}",
    )


def _matches_filters(
    station: dict[str, Any], operators: set[str], plug_types: set[str], min_power: float
) -> bool:
    """Check search filters against the station summary returned by the API."""
    station_operators = {
        str(station[field])
        for field in ("operator", "operatorCode")
        if station.get(field)
    }
    if operators and not operators.intersection(station_operators):
        return False
    if plug_types:
        available = {
            str(value)
            for field in ("plugTypes", "plugTypeNames")
            for value in (station.get(field) or [])
        }
        if not plug_types.intersection(available):
            return False
    power = station.get("maxPowerInKw")
    return not min_power or (
        isinstance(power, (int, float)) and power >= min_power
    )


class EnbwChargeStationsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EnBW Charge Stations."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._api_key: str = ""
        self._require_api_key = False
        self._latitude: float = 0
        self._longitude: float = 0
        self._location_selected = False
        self._search_radius_m: float = DEFAULT_SEARCH_RADIUS_M
        self._station_options: list[SelectOptionDict] = []
        self._search_results: list[dict[str, Any]] = []
        self._station_names: dict[str, str] = {}
        self._operator_filter: set[str] = set()
        self._plug_types_filter: set[str] = set()
        self._min_power_in_kw = 0.0

    def _client(self) -> EnbwApiClient:
        return EnbwApiClient(async_get_clientsession(self.hass), self._api_key)

    def _existing_api_key(self) -> str | None:
        """Return the API key of an already configured charge station, if any."""
        for entry in self._async_current_entries():
            if api_key := entry.data.get(API_KEY):
                return api_key
        return None

    async def _async_search_stations(self) -> list[dict[str, Any]]:
        """Search stations around the configured location."""
        client = self._client()
        radius_km = self._search_radius_m / 1000
        # Use a conservative latitude bound so stations at the radius edge
        # are not clipped by the API's rectangular search area.
        lat_delta = radius_km / 110.5
        lon_delta = radius_km / (111.2 * max(cos(radians(self._latitude)), 0.01))
        stations = await client.async_get_charge_stations(
            self._latitude - lat_delta,
            self._longitude - lon_delta,
            self._latitude + lat_delta,
            self._longitude + lon_delta,
        )

        nearby: dict[str, dict[str, Any]] = {}
        for station in stations:
            if (
                station.get("stationId") is None
                or station.get("lat") is None
                or station.get("lon") is None
            ):
                continue
            if distance(
                self._latitude, self._longitude, station["lat"], station["lon"]
            ) <= self._search_radius_m:
                nearby[str(station["stationId"])] = station
        return list(nearby.values())

    def _filtered_station_options(self) -> list[SelectOptionDict]:
        """Filter and rank the cached search results."""
        scored = [
            (
                station,
                distance(
                    self._latitude, self._longitude, station["lat"], station["lon"]
                ),
            )
            for station in self._search_results
            if _matches_filters(
                station,
                self._operator_filter,
                self._plug_types_filter,
                self._min_power_in_kw,
            )
        ]
        scored.sort(key=lambda item: item[1])
        nearest = scored
        self._station_names = {
            str(station["stationId"]): station_display_name(
                station, str(station["stationId"])
            )
            for station, _ in nearest
        }
        return [_station_option(station, dist) for station, dist in nearest]

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        existing_api_key = self._existing_api_key()

        if user_input is not None:
            self._api_key = user_input.get(API_KEY) or existing_api_key or ""
            location = user_input[LOCATION]
            self._latitude = location["latitude"]
            self._longitude = location["longitude"]
            self._location_selected = True
            self._search_radius_m = location.get("radius", DEFAULT_SEARCH_RADIUS_M)
            try:
                self._search_results = await self._async_search_stations()
            except EnbwAuthError:
                errors["base"] = "invalid_auth"
                self._require_api_key = True
            except EnbwApiError:
                errors["base"] = "cannot_connect"
            else:
                if not self._search_results:
                    errors["base"] = "no_stations_found"
                else:
                    return await self.async_step_filter_stations()

        # The API key comes first, the search area map below it.
        schema: dict[Any, Any] = {}
        if not existing_api_key or self._require_api_key:
            schema[vol.Required(API_KEY)] = str
        schema[
            vol.Required(
                LOCATION,
                default={
                    "latitude": (
                        self._latitude if self._location_selected else self.hass.config.latitude
                    ),
                    "longitude": (
                        self._longitude if self._location_selected else self.hass.config.longitude
                    ),
                    "radius": self._search_radius_m,
                },
            )
        ] = LocationSelector(LocationSelectorConfig(radius=True))
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def async_step_filter_stations(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Offer filters derived from the stations in the selected search area."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._operator_filter = set(user_input.get(OPERATOR_FILTER, []))
            self._plug_types_filter = set(user_input.get(PLUG_TYPES_FILTER, []))
            self._min_power_in_kw = user_input.get(MIN_POWER_IN_KW, 0)
            self._station_options = self._filtered_station_options()
            if self._station_options:
                return await self.async_step_search_station()
            errors["base"] = "no_filter_matches"

        operators = sorted(
            {
                station.get("operator") or station.get("operatorCode")
                for station in self._search_results
                if station.get("operator") or station.get("operatorCode")
            },
            key=str.casefold,
        )
        plug_labels: dict[str, str] = {}
        for station in self._search_results:
            codes = station.get("plugTypes") or []
            names = station.get("plugTypeNames") or []
            for index, code in enumerate(codes):
                name = names[index] if index < len(names) else None
                plug_labels[str(code)] = (
                    f"{name} · {code}" if name and name != code else str(code)
                )
            if not codes:
                for name in names:
                    plug_labels[str(name)] = str(name)
        plug_types = [
            SelectOptionDict(value=code, label=label)
            for code, label in sorted(
                plug_labels.items(), key=lambda item: item[1].casefold()
            )
        ]
        schema: dict[Any, Any] = {}
        if operators:
            schema[vol.Optional(OPERATOR_FILTER)] = SelectSelector(
                SelectSelectorConfig(
                    options=operators,
                    multiple=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        if plug_types:
            schema[vol.Optional(PLUG_TYPES_FILTER)] = SelectSelector(
                SelectSelectorConfig(
                    options=plug_types,
                    multiple=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        schema[vol.Optional(MIN_POWER_IN_KW)] = vol.All(
            vol.Coerce(float), vol.Range(min=0)
        )
        return self.async_show_form(
            step_id="filter_stations", data_schema=vol.Schema(schema), errors=errors
        )

    async def async_step_search_station(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle selecting a station from the search results."""
        if user_input is not None:
            station_number = user_input[STATION_NUMBER]
            return await self._async_create(
                station_number,
                self._station_names.get(
                    station_number, f"Charge station {station_number}"
                ),
            )

        return self.async_show_form(
            step_id="search_station",
            data_schema=vol.Schema(
                {
                    vol.Required(STATION_NUMBER): SelectSelector(
                        SelectSelectorConfig(
                            options=self._station_options,
                            multiple=False,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )

    async def _async_create(
        self, station_number: str, name: str
    ) -> ConfigFlowResult:
        """Create the config entry for the selected station."""
        await self.async_set_unique_id(station_number)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=name,
            data={
                STATION_NUMBER: station_number,
                API_KEY: self._api_key,
                NAME: name,
            },
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of an existing entry."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            self._api_key = user_input[API_KEY]
            station_number = user_input[STATION_NUMBER].strip()
            if any(
                other.entry_id != entry.entry_id and other.unique_id == station_number
                for other in self.hass.config_entries.async_entries(DOMAIN)
            ):
                errors["base"] = "already_configured"
            else:
                try:
                    await self._client().async_get_charge_station(station_number)
                except EnbwAuthError:
                    errors["base"] = "invalid_auth"
                except EnbwApiError:
                    errors["base"] = "cannot_connect"
                else:
                    previous = entry.data.get(PREVIOUS_STATION_NUMBER)
                    if entry.data[STATION_NUMBER] != station_number:
                        previous = entry.data[STATION_NUMBER]
                    new_data = {
                        NAME: user_input[NAME],
                        STATION_NUMBER: station_number,
                        API_KEY: self._api_key,
                    }
                    if previous:
                        new_data[PREVIOUS_STATION_NUMBER] = previous
                    return self.async_update_reload_and_abort(
                        entry,
                        unique_id=station_number,
                        title=user_input[NAME],
                        data=new_data,
                    )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        NAME, default=entry.data.get(NAME, "Charge Station")
                    ): str,
                    vol.Required(
                        STATION_NUMBER, default=entry.data.get(STATION_NUMBER, "")
                    ): str,
                    vol.Required(
                        API_KEY, default=entry.data.get(API_KEY, "")
                    ): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle re-authentication when the API key is rejected."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm re-authentication with a new API key."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            self._api_key = user_input[API_KEY]
            try:
                await self._client().async_get_charge_station(
                    entry.data[STATION_NUMBER]
                )
            except EnbwAuthError:
                errors["base"] = "invalid_auth"
            except EnbwApiError:
                errors["base"] = "cannot_connect"
            else:
                old_key = entry.data[API_KEY]
                for other in self.hass.config_entries.async_entries(DOMAIN):
                    if (
                        other.entry_id == entry.entry_id
                        or other.data.get(API_KEY) != old_key
                    ):
                        continue
                    self.hass.config_entries.async_update_entry(
                        other, data={**other.data, API_KEY: self._api_key}
                    )
                    await self.hass.config_entries.async_reload(other.entry_id)
                return self.async_update_reload_and_abort(
                    entry,
                    data={**entry.data, API_KEY: self._api_key},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(API_KEY): str}),
            errors=errors,
        )
