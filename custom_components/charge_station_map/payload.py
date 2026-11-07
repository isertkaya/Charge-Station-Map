"""Helpers for timestamps supplied by the charge station API."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def point_updated_at(point: dict[str, Any]) -> datetime | None:
    """Return the time of a charge point's last reported state change."""
    value = (point.get("state") or {}).get("updatedAt")
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    try:
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def station_updated_at(data: dict[str, Any]) -> datetime | None:
    """Return the newest known charge point state change for a station."""
    values = (
        updated_at
        for point in data.get("chargePoints", [])
        if isinstance(point, dict)
        if (updated_at := point_updated_at(point)) is not None
    )
    return max(values, default=None)
