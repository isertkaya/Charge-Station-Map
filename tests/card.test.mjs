import assert from "node:assert/strict";
import { test } from "node:test";

class FakeNode {
  constructor(tag = "div") {
    this.tagName = tag;
    this.children = [];
    this.className = "";
    this.textContent = "";
    this.attributes = {};
    this.listeners = {};
    this.events = [];
    this.style = { setProperty() {} };
  }

  append(...nodes) {
    this.children.push(...nodes);
  }

  prepend(...nodes) {
    this.children.unshift(...nodes);
  }

  replaceChildren(...nodes) {
    this.children = [...nodes];
  }

  get firstChild() {
    return this.children[0];
  }

  setAttribute(name, value) {
    this.attributes[name] = value;
  }

  addEventListener(name, listener) {
    (this.listeners[name] ||= []).push(listener);
  }

  click() {
    for (const listener of this.listeners.click || []) listener();
  }

  change() {
    for (const listener of this.listeners.change || []) listener();
  }

  dispatchEvent(event) {
    this.events.push(event);
    return true;
  }
}

class FakeHTMLElement extends FakeNode {
  attachShadow() {
    const card = new FakeNode("ha-card");
    const body = new FakeNode("div");
    const children = [];
    this.shadowRoot = {
      card,
      body,
      children,
      querySelector: (selector) => selector === "ha-card" ? card : body,
      append(...nodes) { children.push(...nodes); },
      set innerHTML(_) {},
    };
    return this.shadowRoot;
  }
}

globalThis.HTMLElement = FakeHTMLElement;
globalThis.document = { createElement: (tag) => new FakeNode(tag) };
globalThis.window = { customCards: [] };
const registered = new Map();
globalThis.customElements = {
  get: (name) => registered.get(name),
  define: (name, klass) => registered.set(name, klass),
};

await import("../custom_components/charge_station_map/www/charge-station-map-card.js");

function textOf(node) {
  return [node.textContent, ...node.children.map(textOf)].join(" ");
}

function findAll(node, className) {
  return [
    ...(node.className.split(" ").includes(className) ? [node] : []),
    ...node.children.flatMap((child) => findAll(child, className)),
  ];
}

function findTags(node, tagName) {
  return [
    ...(node.tagName === tagName ? [node] : []),
    ...node.children.flatMap((child) => findTags(child, tagName)),
  ];
}

function hassFixture() {
  return {
    language: "de",
    locale: { language: "de-DE" },
    config: { time_zone: "Europe/Berlin" },
    states: {
      "binary_sensor.station_renamed": {
        entity_id: "binary_sensor.station_renamed",
        state: "on",
        last_updated: "2026-11-06T10:00:00Z",
        attributes: {
          stationid: "2137426",
          operator: "Wirelane GmbH",
          address: "Quettinger Str. 106",
          availableChargePoints: 1,
          totalChargePoints: 2,
        },
      },
      "sensor.custom_point_name_1": {
        entity_id: "sensor.custom_point_name_1",
        state: "AVAILABLE",
        last_updated: "2026-11-06T10:00:00Z",
        attributes: {
          device_class: "enum", evseId: "DE*WLN*EP001941",
          updatedAt: "2026-11-05T10:00:00+00:00",
          maxPowerInKw: [22],
          connectors: [{ plugTypeName: "Typ 2", maxPowerInKw: 22, cableAttached: false }],
        },
      },
      "sensor.custom_point_name_2": {
        entity_id: "sensor.custom_point_name_2",
        state: "OCCUPIED",
        last_updated: "2026-11-06T10:00:00Z",
        attributes: {
          device_class: "enum", evseId: "DE*WLN*EP001942",
          updatedAt: "2026-11-05T11:00:00+00:00",
          maxPowerInKw: [150, 50],
          connectors: [
            { plugTypeName: "CCS", maxPowerInKw: 150, cableAttached: true },
            { plugTypeName: "CHAdeMO", maxPowerInKw: 50, cableAttached: true },
          ],
        },
      },
      "sensor.other_station_point": {
        entity_id: "sensor.other_station_point",
        state: "BLOCKED",
        last_updated: "2026-11-06T10:00:00Z",
        attributes: {
          device_class: "enum", evseId: "DE*OTHER*EP000001",
          updatedAt: "2026-11-05T11:00:00+00:00",
        },
      },
    },
    entities: {
      "binary_sensor.station_renamed": { device_id: "station-a" },
      "sensor.custom_point_name_1": { device_id: "station-a" },
      "sensor.custom_point_name_2": { device_id: "station-a" },
      "sensor.other_station_point": { device_id: "station-b" },
    },
    devices: { "station-a": { name: "Wirelane GmbH · Quettinger Str. 106" } },
  };
}

test("all cards find renamed point entities on the selected station only", () => {
  const hass = hassFixture();
  for (const type of ["charge-station-map-compact-card", "charge-station-map-detail-card", "charge-station-map-chips-card"]) {
    const Card = registered.get(type);
    assert.ok(Card);
    const card = new Card();
    card.setConfig({ entity: "binary_sensor.station_renamed" });
    card.hass = hass;
    const rendered = textOf(card.shadowRoot.body);
    assert.match(rendered, /Wirelane GmbH/);
    assert.match(rendered, type.includes("detail") ? /1\s+von\s+2/ : /1\s*\/\s*2/);
    assert.match(rendered, /Verfügbar/);
    assert.match(rendered, /Belegt/);
    assert.match(rendered, /EP001941/);
    assert.match(rendered, /EP001942/);
    assert.match(rendered, /150 kW/);
    assert.match(rendered, /Typ 2/);
    assert.match(rendered, /CCS/);
    assert.match(rendered, /CHAdeMO/);
    const icons = findTags(card.shadowRoot.body, "ha-icon").map((icon) => icon.attributes.icon);
    assert.ok(icons.includes("mdi:ev-plug-type2"));
    assert.ok(icons.includes("mdi:ev-plug-ccs2"));
    const powerClass = type.includes("compact") ? "power-metric" : "power-badge";
    assert.ok(findAll(card.shadowRoot.body, powerClass).length >= 2);
    assert.doesNotMatch(rendered, /EP000001|Blockiert/);
    if (type.includes("detail")) {
      assert.match(rendered, /Quettinger Str\. 106/);
      assert.match(rendered, /Seit 05\.11\.2026/);
      assert.doesNotMatch(rendered, /Seit 06\.11\.2026/);
    }
  }
});

test("an unavailable point is shown as missing data, not occupied", () => {
  const hass = hassFixture();
  hass.states["sensor.custom_point_name_2"].state = "unavailable";
  const Card = registered.get("charge-station-map-detail-card");
  const card = new Card();
  card.setConfig({ entity: "binary_sensor.station_renamed" });
  card.hass = hass;
  const rendered = textOf(card.shadowRoot.body);
  assert.match(rendered, /Keine Daten/);
  assert.doesNotMatch(rendered, /Belegt/);
});

test("compact card opens station and point details", () => {
  const Card = registered.get("charge-station-map-compact-card");
  const card = new Card();
  card.setConfig({ entity: "binary_sensor.station_renamed" });
  card.hass = hassFixture();
  findAll(card.shadowRoot.body, "header-action")[0].click();
  assert.equal(card.events.at(-1).type, "hass-action");
  assert.equal(card.events.at(-1).detail.config.entity, "binary_sensor.station_renamed");
  findAll(card.shadowRoot.body, "point-action")[1].click();
  assert.equal(card.events.at(-1).detail.config.entity, "sensor.custom_point_name_2");
});

test("detail card shows every connector and opens the selected entity", () => {
  const Card = registered.get("charge-station-map-detail-card");
  const card = new Card();
  card.setConfig({ entity: "binary_sensor.station_renamed" });
  card.hass = hassFixture();
  assert.equal(findAll(card.shadowRoot.body, "point-action").length, 2);
  assert.match(textOf(card.shadowRoot.body), /CCS\s+150 kW Kabel vorhanden/);
  assert.match(textOf(card.shadowRoot.body), /CHAdeMO\s+50 kW Kabel vorhanden/);
  findAll(card.shadowRoot.body, "point-action")[1].click();
  assert.equal(card.events.at(-1).detail.config.entity, "sensor.custom_point_name_2");
  findAll(card.shadowRoot.body, "rail-segment")[0].click();
  assert.equal(card.events.at(-1).detail.config.entity, "sensor.custom_point_name_1");
});

test("chips card shows each point as a clickable tile and can show the status strip", () => {
  const Card = registered.get("charge-station-map-chips-card");
  const card = new Card();
  card.setConfig({ entity: "binary_sensor.station_renamed" });
  card.hass = hassFixture();
  assert.equal(findAll(card.shadowRoot.body, "point-action").length, 2);
  assert.equal(findAll(card.shadowRoot.body, "rail-segment").length, 0);
  assert.match(textOf(card.shadowRoot.body), /150 kW/);
  assert.match(textOf(card.shadowRoot.body), /Belegt/);
  findAll(card.shadowRoot.body, "point-action")[1].click();
  assert.equal(card.events.at(-1).detail.config.entity, "sensor.custom_point_name_2");
  card.setConfig({ entity: "binary_sensor.station_renamed", show_status_strip: true, show_power: false });
  assert.equal(findAll(card.shadowRoot.body, "rail-segment").length, 2);
  assert.equal(findAll(card.shadowRoot.body, "power-badge").length, 0);
});

test("compact power metric and accessible label format fractional kW for the Home Assistant language", () => {
  const hass = hassFixture();
  const point = hass.states["sensor.custom_point_name_1"];
  point.attributes.maxPowerInKw = [11.5];
  point.attributes.connectors[0].maxPowerInKw = 11.5;
  const Card = registered.get("charge-station-map-compact-card");
  const card = new Card();
  card.setConfig({ entity: "binary_sensor.station_renamed" });
  card.hass = hass;
  assert.equal(findAll(card.shadowRoot.body, "power-metric")[0].attributes["aria-label"], "11,5 kW");
  assert.match(findAll(card.shadowRoot.body, "point-action")[0].attributes["aria-label"], /Maximale Ladeleistung: 11,5 kW/);
  card.setConfig({ entity: "binary_sensor.station_renamed", show_power: false });
  assert.equal(findAll(card.shadowRoot.body, "power-metric").length, 0);
  assert.match(textOf(card.shadowRoot.body), /Verfügbar/);
});

test("display options and Home Assistant tap action are respected", () => {
  const Card = registered.get("charge-station-map-detail-card");
  const card = new Card();
  card.setConfig({
    entity: "binary_sensor.station_renamed",
    title: "Mein Ladepark",
    show_address: false,
    show_status_strip: false,
    show_power: false,
    show_status_time: false,
    show_cable: false,
    plug_style: "icon_only",
    tap_action: { action: "navigate", navigation_path: "/dashboard-ev" },
  });
  card.hass = hassFixture();
  const rendered = textOf(card.shadowRoot.body);
  assert.match(rendered, /Mein Ladepark/);
  assert.doesNotMatch(rendered, /Quettinger Str/);
  assert.doesNotMatch(rendered, /150 kW|CHAdeMO|Kabel vorhanden|Seit 05/);
  assert.equal(findAll(card.shadowRoot.body, "rail-segment").length, 0);
  const icons = findTags(card.shadowRoot.body, "ha-icon").map((icon) => icon.attributes.icon);
  assert.ok(icons.includes("mdi:ev-plug-ccs2"));
  findAll(card.shadowRoot.body, "point-action")[0].click();
  assert.deepEqual(card.events.at(-1).detail.config.tap_action, {
    action: "navigate", navigation_path: "/dashboard-ev",
  });
});

test("compact and chips cards never hide extra charge points", () => {
  const hass = hassFixture();
  for (let index = 3; index <= 6; index += 1) {
    const entityId = `sensor.extra_point_${index}`;
    hass.states[entityId] = {
      entity_id: entityId,
      state: "RESERVED",
      last_updated: "2026-11-06T10:00:00Z",
      attributes: {
        device_class: "enum", evseId: `DE*WLN*EP00194${index}`,
        updatedAt: "2026-11-05T10:00:00+00:00",
        connectors: [{ plugTypeName: "Typ 2", maxPowerInKw: 22 }],
        maxPowerInKw: [22],
      },
    };
    hass.entities[entityId] = { device_id: "station-a" };
  }
  for (const type of ["charge-station-map-compact-card", "charge-station-map-chips-card"]) {
    const Card = registered.get(type);
    const card = new Card();
    card.setConfig({ entity: "binary_sensor.station_renamed" });
    card.hass = hass;
    assert.equal(findAll(card.shadowRoot.body, "point-action").length, 6);
    assert.match(textOf(card.shadowRoot.body), /EP001946/);
  }
});

test("visual editor exposes card settings and saves a display change", () => {
  const Editor = registered.get("charge-station-map-card-editor");
  const editor = new Editor();
  editor.setConfig({ entity: "binary_sensor.station_renamed" });
  editor.hass = hassFixture();
  const settings = editor.shadowRoot.children[1];
  assert.match(textOf(settings), /Anzeige und Aktionen/);
  assert.match(textOf(settings), /Steckeranzeige/);
  const addressCheckbox = findTags(settings, "input")[1];
  addressCheckbox.checked = false;
  addressCheckbox.change();
  assert.equal(editor.events.at(-1).type, "config-changed");
  assert.equal(editor.events.at(-1).detail.config.show_address, false);
  const [plugSelect, tapSelect] = findTags(settings, "select");
  plugSelect.value = "icon_only";
  plugSelect.change();
  assert.equal(editor.events.at(-1).detail.config.plug_style, "icon_only");
  tapSelect.value = "navigate";
  tapSelect.change();
  assert.deepEqual(editor.events.at(-1).detail.config.tap_action, {
    action: "navigate", navigation_path: "",
  });
});
