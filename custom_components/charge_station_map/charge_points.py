"""Helpers shared by charge point entities."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any


def iter_charge_points(
    data: dict[str, Any] | None,
) -> Iterator[tuple[str, int, int | float]]:
    """Yield stable EVSE IDs with their display index and connector power."""
    for index, point in enumerate((data or {}).get("chargePoints") or [], start=1):
        point_id = point.get("evseId") if isinstance(point, dict) else None
        if not isinstance(point_id, str) or not point_id:
            continue
        power = max(
            (
                connector["maxPowerInKw"]
                for connector in (point.get("connectors") or [])
                if isinstance(connector, dict)
                and isinstance(connector.get("maxPowerInKw"), (int, float))
            ),
            default=0,
        )
        yield point_id, index, power


def find_charge_point(
    data: dict[str, Any] | None, point_id: str
) -> dict[str, Any] | None:
    """Find an EVSE in the current station response."""
    for point in (data or {}).get("chargePoints") or []:
        if isinstance(point, dict) and point.get("evseId") == point_id:
            return point
    return None


def charge_point_status(point: dict[str, Any]) -> str | None:
    """Return the exact status reported by the API."""
    status = point.get("status") or (point.get("state") or {}).get("value")
    return status if isinstance(status, str) and status else None
