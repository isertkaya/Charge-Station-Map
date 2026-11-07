"""Display names for charge stations."""

from __future__ import annotations

from typing import Any


def station_display_name(station: dict[str, Any], station_number: str) -> str:
    """Show the operator before the address for a charge station."""
    operator = station.get("operator") or station.get("operatorCode") or "Unknown operator"
    address = station.get("shortAddress") or f"Charge station {station_number}"
    return f"{operator} · {address}"
