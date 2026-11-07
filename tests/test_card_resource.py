"""The dashboard card resource is registered once and upgraded in place."""

from types import SimpleNamespace

import pytest

from custom_components.charge_station_map import (
    CARD_URL,
    _async_register_card_resource,
)
from custom_components.charge_station_map.const import CARD_VERSION


class FakeResources:
    def __init__(self, items=None):
        self.items = list(items or [])
        self.loaded = False

    async def async_get_info(self):
        self.loaded = True
        return {"resources": len(self.items)}

    def async_items(self):
        assert self.loaded, "resource storage must be loaded before it is read"
        return self.items

    async def async_create_item(self, data):
        self.items.append({"id": "card", "type": data["res_type"], "url": data["url"]})

    async def async_update_item(self, item_id, updates):
        item = next(item for item in self.items if item["id"] == item_id)
        item.update(type=updates["res_type"], url=updates["url"])


@pytest.mark.asyncio
async def test_card_resource_is_added_only_once():
    resources = FakeResources([{"id": "other", "type": "module", "url": "/other.js"}])
    hass = SimpleNamespace(data={"lovelace": SimpleNamespace(resource_mode="storage", resources=resources)})

    await _async_register_card_resource(hass)
    await _async_register_card_resource(hass)

    assert resources.items == [
        {"id": "other", "type": "module", "url": "/other.js"},
        {"id": "card", "type": "module", "url": f"{CARD_URL}?v={CARD_VERSION}"},
    ]


@pytest.mark.asyncio
async def test_existing_manual_resource_is_upgraded():
    resources = FakeResources([{"id": "manual", "type": "module", "url": CARD_URL}])
    hass = SimpleNamespace(data={"lovelace": SimpleNamespace(resource_mode="storage", resources=resources)})

    await _async_register_card_resource(hass)

    assert resources.items == [
        {"id": "manual", "type": "module", "url": f"{CARD_URL}?v={CARD_VERSION}"}
    ]


@pytest.mark.asyncio
async def test_yaml_resources_are_left_to_the_user():
    resources = FakeResources()
    hass = SimpleNamespace(data={"lovelace": SimpleNamespace(resource_mode="yaml", resources=resources)})

    await _async_register_card_resource(hass)

    assert not resources.loaded
    assert resources.items == []
