"""Constants for the EnBW charge stations component."""

DOMAIN = "charge_station_map"
CARD_VERSION = "3.10.0"

# Config entry keys
STATION_NUMBER = "station_number"
PREVIOUS_STATION_NUMBER = "previous_station_number"
NAME = "name"
LOCATION = "location"
API_KEY = "api_key"
OPERATOR_FILTER = "operator_filter"
PLUG_TYPES_FILTER = "plug_types_filter"
MIN_POWER_IN_KW = "min_power_in_kw"

# Default radius of the search area on the map, in meters.
DEFAULT_SEARCH_RADIUS_M = 5000

# Extra state attribute keys
ATTR_CABLE_ATTACHED = "cableAttached"
ATTR_CONNECTORS = "connectors"
ATTR_PLUG_TYPE_NAME = "plugTypeName"
ATTR_MAX_POWER_IN_KW = "maxPowerInKw"
ATTR_MAX_POWER_PER_PLUG_TYPE_IN_KW = "maxPowerInKwPerPlugType"
ATTR_EVSE_ID = "evseId"
ATTR_STATE = "state"
ATTR_STATION_ID = "stationid"
ATTR_LATITUDE = "latitude"
ATTR_LONGITUDE = "longitude"
ATTR_ADDRESS = "address"
ATTR_OPERATOR = "operator"
ATTR_UPDATED_AT = "updatedAt"
ATTR_AVAILABLE_CHARGE_POINTS = "availableChargePoints"
ATTR_TOTAL_CHARGE_POINTS = "totalChargePoints"
ATTR_OUT_OF_SERVICE = "isOutOfService"
ATTR_ALWAYS_OPEN = "alwaysOpen"
ATTR_CLOSED_ON_HOLIDAYS = "closedOnHolidays"
ATTR_OPENING_HOURS = "openingHours"
ATTR_NEXT_OPENING_TIME = "nextOpeningTime"
ATTR_NEXT_CLOSING_TIME = "nextClosingTime"
