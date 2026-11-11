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

function legacyHassFixture() {
  const hass = hassFixture();
  hass.states = {
    "binary_sensor.legacy_station": {
      entity_id: "binary_sensor.legacy_station", state: "on",
      attributes: {
        device_class: "presence", stationid: "2137426",
        address: "Quettinger Str. 106", availableChargePoints: 1,
        totalChargePoints: 2,
      },
    },
    "binary_sensor.legacy_point_1": {
      entity_id: "binary_sensor.legacy_point_1", state: "off",
      attributes: {
        device_class: "occupancy", evseId: "DE*WLN*EP001941",
        state: "AVAILABLE", plugTypeName: ["Typ 2"], maxPowerInKw: [22],
        cableAttached: [false], updatedAt: "2026-11-06T10:00:00Z",
      },
    },
    "binary_sensor.legacy_point_2": {
      entity_id: "binary_sensor.legacy_point_2", state: "on",
      attributes: {
        device_class: "occupancy", evseId: "DE*WLN*EP001942",
        state: "RESERVED", plugTypeName: ["CCS", "CHAdeMO"],
        maxPowerInKw: [150, 50], cableAttached: [true, false],
        updatedAt: "2026-11-06T10:00:00Z",
      },
    },
    "binary_sensor.other_legacy_point": {
      entity_id: "binary_sensor.other_legacy_point", state: "on",
      attributes: { device_class: "occupancy", evseId: "DE*OTHER*EP000001", state: "BLOCKED" },
    },
  };
  hass.entities = {
    "binary_sensor.legacy_station": { device_id: "legacy-station-a" },
    "binary_sensor.legacy_point_1": { device_id: "legacy-station-a" },
    "binary_sensor.legacy_point_2": { device_id: "legacy-station-a" },
    "binary_sensor.other_legacy_point": { device_id: "legacy-station-b" },
  };
  hass.devices = { "legacy-station-a": { name: "Quettinger Str. 106" } };
  hass.formatEntityState = () => "Ein";
  return hass;
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

test("all cards show the old EnBW device and its exact charge point states", () => {
  const hass = legacyHassFixture();
  for (const type of ["charge-station-map-compact-card", "charge-station-map-detail-card", "charge-station-map-chips-card"]) {
    const Card = registered.get(type);
    assert.equal(Card.getStubConfig(hass).entity, "binary_sensor.legacy_station");
    const card = new Card();
    card.hass = hass;
    card.setConfig({ entity: "binary_sensor.legacy_station" });
    const rendered = textOf(card.shadowRoot.body);
    assert.match(rendered, /Quettinger Str\. 106/);
    assert.match(rendered, /Verfügbar|Reserviert/);
    assert.match(rendered, /Verfügbar/);
    assert.match(rendered, /Reserviert/);
    assert.match(rendered, /Typ 2|CCS/);
    assert.match(rendered, /150 kW/);
    assert.match(rendered, /Zeit unbekannt/);
    assert.doesNotMatch(rendered, /DE\*OTHER|Blockiert|Seit 06\.11\.2026|Ein/);
    assert.equal(findAll(card.shadowRoot.body, "point-action").length, 2);
    const icons = findTags(card.shadowRoot.body, "ha-icon").map((icon) => icon.attributes.icon);
    assert.ok(icons.includes("mdi:ev-plug-ccs2"));
    if (type.includes("detail")) {
      assert.match(rendered, /Kabel vorhanden|Kein Kabel/);
    }
  }
});

test("legacy point visibility uses EVSE IDs and opens the original entity", () => {
  const hass = legacyHassFixture();
  const card = new (registered.get("charge-station-map-compact-card"))();
  card.hass = hass;
  card.setConfig({
    entity: "binary_sensor.legacy_station",
    hidden_charge_points: ["DE*WLN*EP001941"],
  });
  assert.equal(findAll(card.shadowRoot.body, "point-action").length, 1);
  assert.match(textOf(card.shadowRoot.body), /0\s*\/\s*1/);
  findAll(card.shadowRoot.body, "point-action")[0].click();
  assert.equal(card.events.at(-1).detail.config.entity, "binary_sensor.legacy_point_2");
});

test("all cards hide selected charge points across counts, strip and rows", () => {
  const hass = hassFixture();
  for (const type of ["charge-station-map-compact-card", "charge-station-map-detail-card", "charge-station-map-chips-card"]) {
    const Card = registered.get(type);
    const card = new Card();
    card.hass = hass;
    card.setConfig({
      entity: "binary_sensor.station_renamed",
      hidden_charge_points: ["DE*WLN*EP001941"],
      show_status_strip: true,
    });
    const rendered = textOf(card.shadowRoot.body);
    assert.match(rendered, type.includes("detail") ? /0\s+von\s+1/ : /0\s*\/\s*1/);
    assert.doesNotMatch(rendered, /EP001941|Typ 2|Verfügbar/);
    assert.match(rendered, /EP001942|Belegt/);
    assert.equal(findAll(card.shadowRoot.body, "point-action").length, 1);
    assert.equal(findAll(card.shadowRoot.body, "rail-segment").length, 1);
    assert.equal(card.getCardSize(), type.includes("detail") ? 7 : type.includes("chips") ? 5 : 4);
  }
});

test("all-hidden and newly discovered charge points render predictably", () => {
  const hass = hassFixture();
  for (const type of ["charge-station-map-compact-card", "charge-station-map-detail-card", "charge-station-map-chips-card"]) {
    const Card = registered.get(type);
    const card = new Card();
    card.hass = hass;
    card.setConfig({
      entity: "binary_sensor.station_renamed",
      hidden_charge_points: ["DE*WLN*EP001941", "DE*WLN*EP001942"],
    });
    assert.match(textOf(card.shadowRoot.body), /Alle Ladepunkte dieser Karte sind ausgeblendet/);
    assert.equal(findAll(card.shadowRoot.body, "point-action").length, 0);
    hass.states["sensor.new_point"] = {
      entity_id: "sensor.new_point", state: "AVAILABLE",
      attributes: { device_class: "enum", evseId: "DE*WLN*EP001943", connectors: [] },
    };
    hass.entities["sensor.new_point"] = { device_id: "station-a" };
    card.hass = hass;
    assert.match(textOf(card.shadowRoot.body), /EP001943/);
    assert.equal(findAll(card.shadowRoot.body, "point-action").length, 1);
    delete hass.states["sensor.new_point"];
    delete hass.entities["sensor.new_point"];
  }
});

test("fallback entity IDs also hide charge points", () => {
  const card = new (registered.get("charge-station-map-compact-card"))();
  card.hass = hassFixture();
  card.setConfig({
    entity: "binary_sensor.station_renamed",
    hidden_charge_points: ["sensor.custom_point_name_2"],
  });
  assert.equal(findAll(card.shadowRoot.body, "point-action").length, 1);
  assert.match(textOf(card.shadowRoot.body), /EP001941/);
  assert.doesNotMatch(textOf(card.shadowRoot.body), /EP001942/);
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

test("filtered availability stays unknown when the selected point has no data", () => {
  const hass = hassFixture();
  hass.states["sensor.custom_point_name_2"].state = "unavailable";
  const card = new (registered.get("charge-station-map-compact-card"))();
  card.hass = hass;
  card.setConfig({
    entity: "binary_sensor.station_renamed",
    hidden_charge_points: ["DE*WLN*EP001941"],
  });
  assert.match(textOf(card.shadowRoot.body), /—\s*\/\s*1/);
  assert.match(textOf(card.shadowRoot.body), /Keine Daten/);
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

test("native editor filters station entities, keeps defaults, and preserves focus across changes", () => {
  const Editor = registered.get("charge-station-map-card-editor");
  const editor = new Editor();
  editor.setConfig({ entity: "binary_sensor.station_renamed" });
  editor.hass = hassFixture();
  const form = editor._form;
  assert.equal(form.tagName, "ha-form");
  assert.deepEqual(form.schema[0].selector.entity.include_entities, ["binary_sensor.station_renamed"]);
  assert.equal(form.schema[1].selector.select.multiple, true);
  assert.deepEqual(form.schema[1].selector.select.options.map((option) => option.value), [
    "DE*WLN*EP001941", "DE*WLN*EP001942",
  ]);
  assert.match(form.schema[1].selector.select.options[1].label, /CCS.*150 kW/);
  assert.equal(form.schema[3].title, "Darstellung");
  assert.equal(form.schema[3].expanded, true);
  assert.equal(form.schema[4].title, "Interaktion");
  assert.equal(form.data.show_address, true);
  assert.equal(form.data.show_power, true);
  assert.equal(form.computeLabel({ name: "show_power" }), "Ladeleistung anzeigen");
  const next = {
    ...form.data,
    show_address: false,
    plug_style: "icon_only",
    tap_action: { action: "navigate", navigation_path: "/dashboard-ev" },
  };
  form.listeners["value-changed"][0]({ detail: { value: next }, stopPropagation() {} });
  assert.equal(editor.events.at(-1).type, "config-changed");
  assert.equal(editor.events.at(-1).detail.config.show_address, false);
  assert.equal(editor.events.at(-1).detail.config.plug_style, "icon_only");
  assert.deepEqual(editor.events.at(-1).detail.config.tap_action, {
    action: "navigate", navigation_path: "/dashboard-ev",
  });
  editor.setConfig(editor.events.at(-1).detail.config);
  assert.equal(editor._form, form);
  assert.equal(form.data.show_address, false);
  assert.equal(form.data.plug_style, "icon_only");
});

test("editor saves stable point IDs and clears hidden points when changing station", () => {
  const Editor = registered.get("charge-station-map-card-editor");
  const editor = new Editor();
  editor.setConfig({
    entity: "binary_sensor.station_renamed",
    hidden_charge_points: ["sensor.custom_point_name_1"],
  });
  editor.hass = hassFixture();
  assert.deepEqual(editor._form.data.hidden_charge_points, ["DE*WLN*EP001941"]);
  editor._form.listeners["value-changed"][0]({
    detail: { value: {
      ...editor._form.data,
      hidden_charge_points: ["DE*WLN*EP001941", "DE*WLN*EP001942"],
    } },
    stopPropagation() {},
  });
  assert.deepEqual(editor.events.at(-1).detail.config.hidden_charge_points, [
    "DE*WLN*EP001941", "DE*WLN*EP001942",
  ]);
  editor._form.listeners["value-changed"][0]({
    detail: { value: { ...editor._form.data, entity: "binary_sensor.other_station" } },
    stopPropagation() {},
  });
  assert.deepEqual(editor.events.at(-1).detail.config.hidden_charge_points, []);
});

test("editor offers legacy stations and their charge points", () => {
  const Editor = registered.get("charge-station-map-card-editor");
  const editor = new Editor();
  editor.setConfig({ entity: "binary_sensor.legacy_station" });
  editor.hass = legacyHassFixture();
  assert.deepEqual(editor._form.schema[0].selector.entity.include_entities, ["binary_sensor.legacy_station"]);
  assert.deepEqual(editor._form.schema[1].selector.select.options.map((option) => option.value), [
    "DE*WLN*EP001941", "DE*WLN*EP001942",
  ]);
  assert.match(editor._form.schema[1].selector.select.options[1].label, /CCS.*150 kW/);
});

test("editor lists old and new installations together without mixing points", () => {
  const hass = hassFixture();
  const legacy = legacyHassFixture();
  Object.assign(hass.states, legacy.states);
  Object.assign(hass.entities, legacy.entities);
  Object.assign(hass.devices, legacy.devices);
  const Editor = registered.get("charge-station-map-card-editor");
  const editor = new Editor();
  editor.setConfig({ entity: "binary_sensor.legacy_station" });
  editor.hass = hass;
  assert.deepEqual(new Set(editor._form.schema[0].selector.entity.include_entities), new Set([
    "binary_sensor.station_renamed", "binary_sensor.legacy_station",
  ]));
  assert.equal(editor._form.schema[1].selector.select.options.length, 2);
  const card = new (registered.get("charge-station-map-compact-card"))();
  card.hass = hass;
  card.setConfig({ entity: "binary_sensor.legacy_station" });
  assert.equal(findAll(card.shadowRoot.body, "point-action").length, 2);
  findAll(card.shadowRoot.body, "point-action")[0].click();
  assert.equal(card.events.at(-1).detail.config.entity, "binary_sensor.legacy_point_1");
});

test("native editor exposes variant-specific controls and card defaults", () => {
  const Editor = registered.get("charge-station-map-card-editor");
  const chips = new Editor();
  chips.chips = true;
  chips.setConfig({ entity: "binary_sensor.station_renamed" });
  chips.hass = hassFixture();
  assert.equal(chips._form.data.show_status_strip, false);
  const detail = new Editor();
  detail.detailed = true;
  detail.setConfig({ entity: "binary_sensor.station_renamed" });
  detail.hass = hassFixture();
  assert.equal(detail._form.data.show_status_strip, true);
  assert.ok(detail._form.schema[3].schema[0].schema.some((field) => field.name === "show_cable"));
  assert.ok(!chips._form.schema[3].schema[0].schema.some((field) => field.name === "show_cable"));
});

test("Home Assistant form editor takes over when ha-form has not loaded", () => {
  const Compact = registered.get("charge-station-map-compact-card");
  const Detail = registered.get("charge-station-map-detail-card");
  const Chips = registered.get("charge-station-map-chips-card");
  assert.equal(Compact.getConfigElement(), undefined);
  const compactForm = Compact.getConfigForm();
  assert.deepEqual(compactForm.schema[0].selector.entity.filter, [
    { integration: "charge_station_map", domain: "binary_sensor" },
    { integration: "enbw_chargestations", domain: "binary_sensor", device_class: "presence" },
  ]);
  assert.deepEqual(compactForm.schema[1].selector.entity.filter, [
    { integration: "charge_station_map", domain: "sensor", device_class: "enum" },
    { integration: "enbw_chargestations", domain: "binary_sensor", device_class: "occupancy" },
  ]);
  assert.equal(compactForm.schema[3].schema[0].schema[1].description.suggested_value, true);
  assert.equal(Chips.getConfigForm().schema[3].schema[0].schema[1].description.suggested_value, false);
  assert.ok(Detail.getConfigForm().schema[3].schema[0].schema.some((field) => field.name === "show_cable"));
  registered.set("ha-form", FakeNode);
  assert.equal(Compact.getConfigElement().tagName, "charge-station-map-card-editor");
  registered.delete("ha-form");
});

test("each card keeps a useful layout while display options change", () => {
  const hass = hassFixture();
  for (const type of ["charge-station-map-compact-card", "charge-station-map-detail-card", "charge-station-map-chips-card"]) {
    const Card = registered.get(type);
    const card = new Card();
    card.hass = hass;
    card.setConfig({
      entity: "binary_sensor.station_renamed",
      show_address: false,
      show_status_strip: false,
      show_power: false,
      show_status_time: false,
      plug_style: "icon_only",
    });
    const reduced = textOf(card.shadowRoot.body);
    assert.match(reduced, /Wirelane GmbH/);
    assert.match(reduced, /Verfügbar/);
    assert.match(reduced, /Belegt/);
    assert.doesNotMatch(reduced, /Quettinger Str|150 kW|Typ 2|vor\s+|Seit\s+/);
    assert.equal(findAll(card.shadowRoot.body, "point-action").length, 2);
    assert.equal(findAll(card.shadowRoot.body, "rail-segment").length, 0);
    card.setConfig({ entity: "binary_sensor.station_renamed" });
    const restored = textOf(card.shadowRoot.body);
    assert.match(restored, /Quettinger Str/);
    assert.match(restored, /150 kW/);
    assert.match(restored, /Typ 2/);
  }
});
