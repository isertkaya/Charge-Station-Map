// Dashboard cards for the Charge Station Map Home Assistant integration.
const CARD_TYPES = [
  ["charge-station-map-compact-card", "Charge Station Map · Kompakt"],
  ["charge-station-map-detail-card", "Charge Station Map · Details"],
  ["charge-station-map-chips-card", "Charge Station Map · Chips"],
];

const TEXT = {
  de: {
    of: "von",
    points: "Ladepunkten",
    point: "Ladepunkt",
    noData: "Keine Daten",
    noTime: "Zeit unbekannt",
    noPoints: "Noch keine Ladepunkte gefunden",
    selectStation: "Ladestation auswählen",
    missingStation: "Die gewählte Ladestation ist nicht vorhanden.",
    closed: "Ladestation derzeit geschlossen",
    since: "Seit",
    operator: "Betreiber unbekannt",
    station: "Ladestation",
    free: "frei",
    maxPower: "Maximale Ladeleistung",
    plugUnknown: "Stecker unbekannt",
    details: "Details in Home Assistant",
    cable: "Kabel vorhanden",
    noCable: "Kein Kabel",
    editor: {
      settings: "Anzeige und Aktionen",
      title: "Überschrift",
      address: "Adresse anzeigen",
      strip: "Statusstreifen anzeigen",
      power: "Ladeleistung anzeigen",
      time: "Statuszeit anzeigen",
      cable: "Kabelangaben anzeigen",
      plugStyle: "Steckeranzeige",
      iconText: "Icon und Name",
      iconOnly: "Nur Icon",
      tap: "Beim Tippen",
      moreInfo: "Home-Assistant-Details öffnen",
      noAction: "Keine Aktion",
      navigate: "Dashboard-Seite öffnen",
      path: "Dashboard-Pfad",
    },
    statuses: {
      AVAILABLE: "Verfügbar",
      OCCUPIED: "Belegt",
      RESERVED: "Reserviert",
      BLOCKED: "Blockiert",
      OUT_OF_SERVICE: "Außer Betrieb",
      UNKNOWN: "Unbekannt",
    },
  },
  en: {
    of: "of",
    points: "charge points",
    point: "Charge point",
    noData: "No data",
    noTime: "Time unknown",
    noPoints: "No charge points found yet",
    selectStation: "Select a charge station",
    missingStation: "The selected charge station is missing.",
    closed: "Charge station currently closed",
    since: "Since",
    operator: "Unknown operator",
    station: "Charge station",
    free: "free",
    maxPower: "Maximum power",
    plugUnknown: "Plug unknown",
    details: "Details in Home Assistant",
    cable: "Cable attached",
    noCable: "No cable",
    editor: {
      settings: "Display and actions",
      title: "Heading",
      address: "Show address",
      strip: "Show status strip",
      power: "Show charging power",
      time: "Show status time",
      cable: "Show cable details",
      plugStyle: "Plug display",
      iconText: "Icon and name",
      iconOnly: "Icon only",
      tap: "On tap",
      moreInfo: "Open Home Assistant details",
      noAction: "No action",
      navigate: "Open dashboard page",
      path: "Dashboard path",
    },
    statuses: {
      AVAILABLE: "Available",
      OCCUPIED: "Occupied",
      RESERVED: "Reserved",
      BLOCKED: "Blocked",
      OUT_OF_SERVICE: "Out of service",
      UNKNOWN: "Unknown",
    },
  },
};

const STYLE = `
  :host { display: block; --csm-free: var(--success-color, #43a047); --csm-busy: var(--error-color, #d84444); --csm-warn: var(--warning-color, #e9a23b); --csm-muted: var(--secondary-text-color, #777); }
  ha-card { overflow: hidden; border-radius: var(--ha-card-border-radius, 16px); }
  .body { padding: 18px; color: var(--primary-text-color); }
  button { font: inherit; }
  button:focus-visible { outline: 2px solid var(--primary-color, #03a9f4); outline-offset: 2px; }
  .hero { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 14px; align-items: center; }
  .header-action, .point-action, .rail-segment { border: 0; cursor: pointer; color: inherit; }
  .header-action { min-width: 0; padding: 0; background: none; text-align: left; }
  .header-action:hover .operator, .point-action:hover .point-name { text-decoration: underline; }
  .brand { display: flex; gap: 11px; align-items: center; min-width: 0; }
  .brand-copy { min-width: 0; }
  .station-bubble, .plug-bubble { display: inline-grid; flex: none; place-items: center; border-radius: 50%; color: var(--primary-color, #03a9f4); background: var(--secondary-background-color, rgba(127,127,127,.12)); }
  .station-bubble { width: 44px; height: 44px; }
  .station-bubble ha-icon { --mdc-icon-size: 24px; --ha-icon-size: 24px; width: 24px; height: 24px; }
  .plug-bubble { width: 34px; height: 34px; }
  .plug-bubble ha-icon { --mdc-icon-size: 20px; --ha-icon-size: 20px; width: 20px; height: 20px; }
  .plug-icons { display: flex; flex: none; gap: 3px; flex-wrap: wrap; max-width: 75px; }
  .eyebrow { color: var(--csm-muted); font-size: .68rem; letter-spacing: .12em; text-transform: uppercase; font-weight: 700; }
  .operator { margin: 4px 0 0; font-size: 1.12rem; line-height: 1.25; font-weight: 700; overflow-wrap: anywhere; }
  .address { margin-top: 4px; color: var(--csm-muted); font-size: .82rem; line-height: 1.3; overflow-wrap: anywhere; }
  .count { text-align: center; white-space: nowrap; }
  .count strong { font-size: 1.55rem; line-height: 1; font-weight: 750; font-variant-numeric: tabular-nums; }
  .count .out-of { color: var(--csm-muted); font-size: .9rem; }
  .count-label { margin-top: 3px; color: var(--csm-muted); font-size: .75rem; }
  .compact .count { min-width: 72px; padding: 10px; border-radius: 14px; background: var(--secondary-background-color, rgba(127,127,127,.1)); }
  .notice { margin-top: 10px; color: var(--warning-color, #b36b00); font-size: .82rem; }
  .status-rail { display: grid; grid-template-columns: repeat(auto-fit, minmax(7px, 1fr)); gap: 4px; margin-top: 16px; }
  .rail-segment { --state-color: var(--csm-muted); width: 100%; height: 7px; padding: 0; border-radius: 5px; background: var(--state-color); }
  .rail-segment:hover { height: 10px; margin-top: -3px; }
  .point-grid { display: grid; gap: 8px; margin-top: 12px; }
  .point { --state-color: var(--csm-muted); min-width: 0; }
  .point.available, .rail-segment.available, .legend-item.available { --state-color: var(--csm-free); }
  .point.occupied, .rail-segment.occupied, .legend-item.occupied { --state-color: var(--csm-busy); }
  .point.reserved, .point.blocked, .rail-segment.reserved, .rail-segment.blocked, .legend-item.reserved, .legend-item.blocked { --state-color: var(--csm-warn); }
  .point.available .plug-bubble { color: var(--csm-free); background: color-mix(in srgb, var(--csm-free) 14%, transparent); }
  .point.occupied .plug-bubble { color: var(--csm-busy); background: color-mix(in srgb, var(--csm-busy) 14%, transparent); }
  .point.reserved .plug-bubble, .point.blocked .plug-bubble { color: var(--csm-warn); background: color-mix(in srgb, var(--csm-warn) 14%, transparent); }
  .point-action { box-sizing: border-box; width: 100%; height: 100%; padding: 0; text-align: left; }
  .point-name { font-weight: 700; font-size: .91rem; overflow-wrap: anywhere; }
  .point-id { color: var(--csm-muted); font-size: .72rem; overflow-wrap: anywhere; }
  .point-meta { margin-top: 4px; color: var(--csm-muted); font-size: .78rem; overflow-wrap: anywhere; }
  .point-title { display: flex; align-items: center; flex-wrap: wrap; gap: 5px 9px; }
  .power-badge { display: inline-flex; align-items: baseline; gap: 3px; padding: 3px 7px; border-radius: 9px; color: var(--primary-text-color); background: color-mix(in srgb, var(--primary-color, #03a9f4) 15%, var(--card-background-color, #fff)); font-variant-numeric: tabular-nums; white-space: nowrap; }
  .power-badge strong { font-size: .9rem; font-weight: 750; line-height: 1; }
  .power-badge small { font-size: .67rem; font-weight: 700; }
  .point-status { display: inline-flex; gap: 6px; align-items: center; font-size: .83rem; font-weight: 650; white-space: nowrap; }
  .dot { width: 8px; height: 8px; flex: none; border-radius: 50%; background: var(--state-color); }
  .age, .exact-time { color: var(--csm-muted); font-size: .74rem; }
  .empty { margin-top: 12px; color: var(--csm-muted); font-size: .85rem; }
  .compact .point { border-radius: 14px; background: var(--secondary-background-color, rgba(127,127,127,.08)); }
  .compact .point-action { display: flex; gap: 9px; align-items: center; justify-content: space-between; padding: 9px 11px; background: transparent; }
  .compact .point-main { min-width: 0; }
  .compact .point-side { flex: none; text-align: right; max-width: 42%; }
  .compact .point-status { white-space: normal; justify-content: flex-end; }
  .compact .point-meta { overflow-wrap: anywhere; }
  .compact .age { margin-top: 3px; }
  .detail .body { padding: 22px; }
  .detail .operator { font-size: 1.3rem; }
  .detail .gauge { width: 86px; height: 86px; display: grid; place-items: center; border-radius: 50%; background: conic-gradient(var(--csm-free) var(--free-ratio, 0%), var(--divider-color, #ddd) 0); }
  .detail .gauge-inner { display: grid; place-content: center; width: 68px; height: 68px; border-radius: 50%; background: var(--card-background-color, #fff); text-align: center; }
  .detail .gauge strong { font-size: 1.3rem; }
  .detail .legend { display: flex; flex-wrap: wrap; gap: 7px 14px; margin-top: 14px; }
  .legend-item { --state-color: var(--csm-muted); display: inline-flex; gap: 5px; align-items: center; font-size: .75rem; color: var(--csm-muted); }
  .legend-item .dot { width: 7px; height: 7px; }
  .detail .point-grid { grid-template-columns: repeat(auto-fit, minmax(min(100%, 230px), 1fr)); gap: 10px; margin-top: 18px; }
  .detail .point { border-radius: 16px; overflow: hidden; background: var(--secondary-background-color, rgba(127,127,127,.08)); }
  .detail .point-action { display: block; padding: 15px; background: transparent; }
  .detail .point-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }
  .detail .point-status { padding: 4px 7px; border-radius: 8px; background: var(--secondary-background-color, rgba(127,127,127,.1)); }
  .detail .connector-list { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 16px; }
  .connector-chip { display: inline-flex; gap: 6px; align-items: center; padding: 4px 8px 4px 4px; border-radius: 18px; background: var(--card-background-color, #fff); font-size: .75rem; }
  .connector-chip .plug-bubble { width: 25px; height: 25px; }
  .connector-chip ha-icon { --mdc-icon-size: 17px; --ha-icon-size: 17px; width: 17px; height: 17px; }
  .connector-chip .power-badge { padding: 3px 5px; }
  .connector-chip .cable-label { color: var(--csm-muted); }
  .detail .point-bottom { display: flex; justify-content: space-between; align-items: flex-end; gap: 8px; margin-top: 15px; padding-top: 10px; border-top: 1px solid var(--divider-color, #ddd); }
  .detail .exact-time { margin-top: 2px; }
  .open-cue { color: var(--csm-muted); font-size: 1rem; }
  .chips .body { padding: 16px; }
  .chips .station-bubble { width: 40px; height: 40px; }
  .chips .count { min-width: 74px; padding: 8px 10px; border-radius: 20px; background: color-mix(in srgb, var(--csm-free) 15%, var(--card-background-color, #fff)); }
  .chips .count strong { color: var(--csm-free); font-size: 1.25rem; }
  .chips .point-grid { grid-template-columns: repeat(auto-fit, minmax(min(100%, 160px), 1fr)); gap: 8px; margin-top: 14px; }
  .chips .point { border-radius: 16px; background: var(--secondary-background-color, rgba(127,127,127,.08)); box-shadow: inset 3px 0 var(--state-color); }
  .chips .point-action { display: block; min-height: 104px; padding: 11px 12px; background: transparent; }
  .chips .chip-top, .chips .chip-bottom { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
  .chips .chip-top { margin-bottom: 10px; }
  .chips .plug-icons { max-width: none; }
  .chips .plug-bubble { width: 29px; height: 29px; }
  .chips .plug-bubble ha-icon { --mdc-icon-size: 17px; --ha-icon-size: 17px; width: 17px; height: 17px; }
  .chips .power-badge strong { font-size: 1.08rem; }
  .chips .chip-name { margin-top: 2px; color: var(--csm-muted); font-size: .72rem; }
  .chips .point-status { white-space: normal; font-size: .78rem; }
  .chips .age { white-space: nowrap; }
  @media (max-width: 360px) {
    .body, .detail .body { padding: 14px; }
    .hero { gap: 8px; }
    .detail .gauge { width: 70px; height: 70px; }
    .detail .gauge-inner { width: 56px; height: 56px; }
    .compact .point-action { padding: 9px; }
  }
`;

function language(hass) {
  return (hass?.language || "en").toLowerCase().startsWith("de") ? "de" : "en";
}

function element(tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value !== undefined && value !== null) node.textContent = String(value);
  return node;
}

function isStation(state) {
  return state?.entity_id?.startsWith("binary_sensor.") &&
    state.attributes?.stationid != null &&
    state.attributes?.availableChargePoints != null &&
    state.attributes?.totalChargePoints != null;
}

function stations(hass) {
  return Object.values(hass?.states || {}).filter(isStation).sort((a, b) => {
    const nameA = `${a.attributes.operator || ""} ${a.attributes.address || ""}`;
    const nameB = `${b.attributes.operator || ""} ${b.attributes.address || ""}`;
    return nameA.localeCompare(nameB);
  });
}

function pointStates(hass, stationEntityId) {
  const deviceId = hass?.entities?.[stationEntityId]?.device_id;
  if (!deviceId) return [];
  return Object.values(hass.states || {})
    .filter((state) =>
      state.entity_id.startsWith("sensor.") &&
      state.attributes?.evseId &&
      state.attributes?.device_class === "enum" &&
      hass.entities?.[state.entity_id]?.device_id === deviceId
    )
    .sort((a, b) => String(a.attributes.evseId).localeCompare(String(b.attributes.evseId)));
}

function relativeTime(value, locale, now = Date.now()) {
  if (!value) return null;
  const timestamp = Date.parse(value);
  if (!Number.isFinite(timestamp)) return null;
  const elapsed = now - timestamp;
  if (elapsed < -60000) return null;
  const seconds = Math.max(0, Math.floor(elapsed / 1000));
  const formatter = new Intl.RelativeTimeFormat(locale, { numeric: "auto", style: "short" });
  if (seconds < 60) return formatter.format(0, "second");
  if (seconds < 3600) return formatter.format(-Math.floor(seconds / 60), "minute");
  if (seconds < 86400) return formatter.format(-Math.floor(seconds / 3600), "hour");
  return formatter.format(-Math.floor(seconds / 86400), "day");
}

function exactTime(value, locale, timeZone) {
  if (!value) return null;
  const timestamp = Date.parse(value);
  if (!Number.isFinite(timestamp)) return null;
  return new Intl.DateTimeFormat(locale, {
    year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit",
    ...(timeZone ? { timeZone } : {}),
  }).format(timestamp);
}

function statusText(hass, state, strings) {
  if (!state || state.state === "unavailable" || state.state === "unknown") return strings.noData;
  const translated = hass.formatEntityState?.(state);
  if (translated && translated !== state.state) return translated;
  return strings.statuses[state.state] || state.state.replaceAll("_", " ");
}

function count(value) {
  const number = Number(value);
  return Number.isFinite(number) && number >= 0 ? String(number) : "—";
}

function powerValue(point) {
  const powers = Array.isArray(point.attributes?.maxPowerInKw)
    ? point.attributes.maxPowerInKw.filter((value) => typeof value === "number" && Number.isFinite(value))
    : [];
  return powers.length ? Math.max(...powers) : null;
}

function powerBadge(power, locale) {
  if (typeof power !== "number" || !Number.isFinite(power)) return null;
  const badge = element("span", "power-badge");
  const formatted = new Intl.NumberFormat(locale, { maximumFractionDigits: 1 }).format(power);
  badge.setAttribute("aria-label", `${formatted} kW`);
  badge.append(element("strong", "", formatted), element("small", "", "kW"));
  return badge;
}

function connectorsOf(point) {
  return Array.isArray(point.attributes?.connectors)
    ? point.attributes.connectors.filter((connector) => connector && typeof connector === "object")
    : [];
}

function plugNames(point, strings) {
  const names = connectorsOf(point).map((connector) => connector.plugTypeName || connector.plugType)
    .filter(Boolean);
  if (!names.length && Array.isArray(point.attributes?.plugTypeName)) {
    names.push(...point.attributes.plugTypeName.filter(Boolean));
  }
  return [...new Set(names)].join(" + ") || strings.plugUnknown;
}

function plugIcon(type) {
  const value = String(type || "").toUpperCase();
  if (value.includes("CCS") || value.includes("COMBO")) return "mdi:ev-plug-ccs2";
  if (value.includes("CHADEMO")) return "mdi:ev-plug-chademo";
  if (value.includes("TESLA")) return "mdi:ev-plug-tesla";
  if (value.includes("TYPE_1") || value.includes("TYP 1") || value.includes("TYPE 1")) return "mdi:ev-plug-type1";
  if (value.includes("TYPE_2") || value.includes("TYP 2") || value.includes("TYPE 2")) return "mdi:ev-plug-type2";
  return "mdi:ev-station";
}

function plugEntries(point, strings) {
  const connectors = connectorsOf(point);
  if (connectors.length) {
    return connectors.map((connector) => ({
      name: connector.plugTypeName || connector.plugType || strings.plugUnknown,
      power: connector.maxPowerInKw,
      cable: connector.cableAttached,
    }));
  }
  const names = Array.isArray(point.attributes?.plugTypeName)
    ? point.attributes.plugTypeName.filter(Boolean) : [];
  return (names.length ? names : [strings.plugUnknown]).map((name) => ({ name }));
}

function plugBubble(entry) {
  const bubble = element("span", "plug-bubble");
  bubble.title = entry.name;
  bubble.setAttribute("aria-label", entry.name);
  const icon = element("ha-icon");
  icon.setAttribute("icon", plugIcon(entry.name));
  bubble.append(icon);
  return bubble;
}

function visible(config, option) {
  return config?.[option] !== false;
}

function showStatusStrip(config, chips) {
  return chips ? config?.show_status_strip === true : visible(config, "show_status_strip");
}

class ChargeStationMapCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `<style>${STYLE}</style><ha-card><div class="body"></div></ha-card>`;
  }

  static getStubConfig(hass) {
    return { entity: stations(hass)[0]?.entity_id || "" };
  }

  static getConfigElement() {
    const editor = document.createElement("charge-station-map-card-editor");
    editor.detailed = this === ChargeStationMapDetailCard;
    editor.chips = this === ChargeStationMapChipsCard;
    return editor;
  }

  setConfig(config) {
    this._config = { ...config };
    this._signature = undefined;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  connectedCallback() {
    this._timer = setInterval(() => this._render(true), 60000);
  }

  disconnectedCallback() {
    clearInterval(this._timer);
    this._timer = undefined;
  }

  getCardSize() {
    const height = this.shadowRoot.querySelector("ha-card")?.getBoundingClientRect?.().height;
    if (height > 0) return Math.ceil(height / 50);
    const points = pointStates(this._hass, this._config?.entity).length;
    if (this._detailed) return 4 + points * 3;
    if (this._chips) return 3 + Math.ceil(points / 2) * 2;
    return 3 + points;
  }

  getGridOptions() {
    return { columns: 6, min_columns: 3, rows: "auto" };
  }

  _activate(entityId) {
    const tapAction = this._config?.tap_action || { action: "more-info" };
    if (tapAction.action === "none") return;
    this.dispatchEvent(new CustomEvent("hass-action", {
      detail: {
        config: { entity: entityId, tap_action: tapAction },
        action: "tap",
      },
      bubbles: true,
      composed: true,
    }));
  }

  _render(force = false) {
    if (!this._hass || !this._config) return;
    const hass = this._hass;
    const strings = TEXT[language(hass)];
    const locale = hass.locale?.language || hass.language || "en";
    const station = hass.states?.[this._config.entity];
    const points = pointStates(hass, this._config.entity);
    const deviceId = hass.entities?.[this._config.entity]?.device_id;
    const device = hass.devices?.[deviceId];
    const signature = JSON.stringify([
      this._config.entity, station?.state, station?.last_updated,
      device?.name_by_user, device?.name,
      points.map((point) => [point.entity_id, point.state, point.last_updated]),
      locale, hass.config?.time_zone,
    ]);
    if (!force && signature === this._signature) return;
    this._signature = signature;

    const card = this.shadowRoot.querySelector("ha-card");
    card.className = this._detailed ? "detail" : this._chips ? "chips" : "compact";
    const body = this.shadowRoot.querySelector(".body");
    body.replaceChildren();
    if (!this._config.entity) {
      body.append(element("div", "empty", strings.selectStation));
      return;
    }
    if (!station) {
      body.append(element("div", "empty", strings.missingStation));
      return;
    }

    const attrs = station.attributes || {};
    const online = station.state !== "unavailable" && station.state !== "unknown";
    const deviceParts = (device?.name || "").split(" · ");
    const operator = attrs.operator || deviceParts[0] || strings.operator;
    const address = attrs.address || deviceParts.slice(1).join(" · ");
    const headerAction = element("button", "header-action");
    headerAction.type = "button";
    headerAction.title = strings.details;
    headerAction.setAttribute("aria-label", `${strings.details}: ${operator}`);
    headerAction.addEventListener("click", () => this._activate(this._config.entity));
    const brand = element("div", "brand");
    const stationBubble = element("span", "station-bubble");
    const stationIcon = element("ha-icon");
    stationIcon.setAttribute("icon", "mdi:ev-station");
    stationBubble.append(stationIcon);
    const brandCopy = element("div", "brand-copy");
    const title = typeof this._config.title === "string" ? this._config.title.trim() : "";
    brandCopy.append(element("div", "eyebrow", title || strings.station));
    brandCopy.append(element("h3", "operator", operator));
    if (address && visible(this._config, "show_address")) {
      brandCopy.append(element("div", "address", address));
    }
    brand.append(stationBubble, brandCopy);
    headerAction.append(brand);

    const available = online ? count(attrs.availableChargePoints) : "—";
    const total = online ? count(attrs.totalChargePoints) : "—";
    const hero = element("div", "hero");
    hero.append(headerAction);
    if (this._detailed) {
      const gauge = element("div", "gauge");
      const freeCount = Number(attrs.availableChargePoints);
      const totalCount = Number(attrs.totalChargePoints);
      const ratio = online && Number.isFinite(freeCount) && Number.isFinite(totalCount) && totalCount > 0
        ? Math.max(0, Math.min(100, (freeCount / totalCount) * 100)) : 0;
      gauge.style.setProperty("--free-ratio", `${ratio}%`);
      const gaugeInner = element("div", "gauge-inner");
      gaugeInner.append(element("strong", "", available));
      gaugeInner.append(element("div", "count-label", `${strings.of} ${total}`));
      gauge.append(gaugeInner);
      const gaugeContainer = element("div", "count");
      gaugeContainer.append(gauge, element("div", "count-label", strings.free));
      hero.append(gaugeContainer);
    } else {
      const counter = element("div", "count");
      counter.append(element("strong", "", available), element("span", "out-of", ` / ${total}`));
      counter.append(element("div", "count-label", strings.free));
      hero.append(counter);
    }
    body.append(hero);

    if (!online) body.append(element("div", "notice", strings.noData));
    else if (station.state === "off" && Number(attrs.availableChargePoints) > 0) {
      body.append(element("div", "notice", strings.closed));
    }

    if (points.length > 0 && showStatusStrip(this._config, this._chips)) {
      const rail = element("div", "status-rail");
      rail.setAttribute("aria-label", strings.points);
      for (const point of points) {
        const segment = element("button", `rail-segment ${point.state.toLowerCase()}`);
        segment.type = "button";
        segment.title = `${point.attributes.evseId} · ${statusText(hass, point, strings)}`;
        segment.setAttribute("aria-label", segment.title);
        segment.addEventListener("click", () => this._activate(point.entity_id));
        rail.append(segment);
      }
      body.append(rail);
    }

    if (this._detailed && points.length > 0 && showStatusStrip(this._config, this._chips)) {
      const legend = element("div", "legend");
      const statuses = new Map();
      for (const point of points) {
        const item = statuses.get(point.state) || { point, count: 0 };
        item.count += 1;
        statuses.set(point.state, item);
      }
      for (const [status, item] of statuses) {
        const label = element("div", `legend-item ${status.toLowerCase()}`);
        label.append(element("span", "dot"));
        label.append(element("span", "", `${statusText(hass, item.point, strings)} ${item.count}`));
        legend.append(label);
      }
      body.append(legend);
    }

    const list = element("div", "point-grid");
    if (points.length === 0) list.append(element("div", "empty", strings.noPoints));
    points.forEach((point) => {
      const id = String(point.attributes.evseId);
      const shortId = id.split("*").at(-1);
      const entries = plugEntries(point, strings);
      const maxPower = powerValue(point);
      const row = element("div", `point ${point.state.toLowerCase()}`);
      const action = element("button", "point-action");
      action.type = "button";
      action.title = strings.details;
      const powerInfo = maxPower === null ? "" : ` ${strings.maxPower}: ${new Intl.NumberFormat(locale, { maximumFractionDigits: 1 }).format(maxPower)} kW.`;
      action.setAttribute("aria-label", `${strings.point} ${shortId}: ${statusText(hass, point, strings)}. ${plugNames(point, strings)}.${powerInfo} ${strings.details}`);
      action.addEventListener("click", () => this._activate(point.entity_id));
      const statusNode = element("div", "point-status");
      statusNode.append(element("span", "dot"), element("span", "", statusText(hass, point, strings)));
      const updatedAt = point.attributes.updatedAt;
      const relative = relativeTime(updatedAt, locale);
      const exact = exactTime(updatedAt, locale, hass.config?.time_zone);
      const time = point.state === "unavailable" || point.state === "unknown" ? null : exact;
      if (this._chips) {
        const icons = element("div", "plug-icons");
        for (const entry of entries.filter((entry, index, all) => all.findIndex((other) => other.name === entry.name) === index)) {
          icons.append(plugBubble(entry));
        }
        const top = element("div", "chip-top");
        top.append(icons);
        if (visible(this._config, "show_power")) {
          const badge = powerBadge(maxPower, locale);
          if (badge) top.append(badge);
        }
        const bottom = element("div", "chip-bottom");
        bottom.append(statusNode);
        if (visible(this._config, "show_status_time")) {
          bottom.append(element("span", "age", time ? (relative || `${strings.since} ${time}`) : strings.noTime));
        }
        const plugLabel = this._config.plug_style === "icon_only" ? "" : ` · ${plugNames(point, strings)}`;
        action.append(top, bottom, element("div", "chip-name", `${shortId}${plugLabel}`));
      } else if (this._detailed) {
        const top = element("div", "point-top");
        const heading = element("div");
        heading.append(element("div", "point-name", shortId));
        heading.append(element("div", "point-id", id));
        top.append(heading, statusNode);
        action.append(top);
        const connectorList = element("div", "connector-list");
        for (const entry of entries) {
          const chip = element("span", "connector-chip");
          chip.title = entry.name;
          chip.append(plugBubble(entry));
          if (this._config.plug_style !== "icon_only") chip.append(element("span", "", entry.name));
          if (visible(this._config, "show_power")) {
            const badge = powerBadge(entry.power, locale);
            if (badge) chip.append(badge);
          }
          if (visible(this._config, "show_cable") && entry.cable === true) {
            chip.append(element("span", "cable-label", strings.cable));
          }
          if (visible(this._config, "show_cable") && entry.cable === false) {
            chip.append(element("span", "cable-label", strings.noCable));
          }
          connectorList.append(chip);
        }
        action.append(connectorList);
        if (visible(this._config, "show_status_time")) {
          const bottom = element("div", "point-bottom");
          const when = element("div");
          when.append(element("div", "age", time ? (relative || `${strings.since} ${time}`) : strings.noTime));
          if (time) when.append(element("div", "exact-time", `${strings.since} ${time}`));
          bottom.append(when, element("span", "open-cue", "↗"));
          action.append(bottom);
        }
      } else {
        const icons = element("div", "plug-icons");
        for (const entry of entries.filter((entry, index, all) => all.findIndex((other) => other.name === entry.name) === index)) {
          icons.append(plugBubble(entry));
        }
        const main = element("div", "point-main");
        const titleLine = element("div", "point-title");
        titleLine.append(element("span", "point-name", shortId));
        if (visible(this._config, "show_power")) {
          const badge = powerBadge(maxPower, locale);
          if (badge) titleLine.append(badge);
        }
        main.append(titleLine);
        if (this._config.plug_style !== "icon_only") {
          main.append(element("div", "point-meta", plugNames(point, strings)));
        }
        const side = element("div", "point-side");
        side.append(statusNode);
        if (visible(this._config, "show_status_time")) {
          side.append(element("div", "age", time ? (relative || `${strings.since} ${time}`) : strings.noTime));
        }
        action.append(icons, main, side);
      }
      row.append(action);
      list.append(row);
    });
    body.append(list);
  }
}

class ChargeStationMapCompactCard extends ChargeStationMapCard {
  _detailed = false;
}

class ChargeStationMapDetailCard extends ChargeStationMapCard {
  _detailed = true;
}

class ChargeStationMapChipsCard extends ChargeStationMapCard {
  _chips = true;
}

class ChargeStationMapCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  setConfig(config) {
    this._config = { ...config };
    this._signature = undefined;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _changed(patch) {
    this._config = { ...this._config, ...patch };
    this.dispatchEvent(new CustomEvent("config-changed", {
      detail: { config: this._config },
      bubbles: true,
      composed: true,
    }));
  }

  _render() {
    if (!this._hass || !this._config) return;
    const strings = TEXT[language(this._hass)];
    const options = stations(this._hass);
    const signature = JSON.stringify([
      this._config.entity,
      language(this._hass),
      this._config.title,
      this._config.show_address,
      this._config.show_status_strip,
      this._config.show_power,
      this._config.show_status_time,
      this._config.show_cable,
      this._config.plug_style,
      this._config.tap_action,
      options.map((station) => [station.entity_id, station.attributes.operator, station.attributes.address]),
    ]);
    if (signature === this._signature) return;
    this._signature = signature;
    this.shadowRoot.innerHTML = `<style>
      label { display: block; margin: 12px 0 6px; color: var(--primary-text-color); }
      select, input[type="text"] { width: 100%; box-sizing: border-box; padding: 10px; border-radius: 8px;
        color: var(--primary-text-color); background: var(--card-background-color);
        border: 1px solid var(--divider-color); }
      details { margin-top: 18px; color: var(--primary-text-color); }
      summary { cursor: pointer; font-weight: 600; }
      .check { display: flex; align-items: center; gap: 10px; }
      .check input { margin: 0; accent-color: var(--primary-color); }
    </style>`;
    const label = element("label", "", strings.selectStation);
    const select = element("select");
    select.append(element("option", "", "—"));
    select.firstChild.value = "";
    for (const station of options) {
      const option = element("option", "", `${station.attributes.operator || strings.operator} · ${station.attributes.address || station.attributes.stationid}`);
      option.value = station.entity_id;
      select.append(option);
    }
    if (this._config.entity && !options.some((station) => station.entity_id === this._config.entity)) {
      const option = element("option", "", this._config.entity);
      option.value = this._config.entity;
      select.append(option);
    }
    select.value = this._config.entity || "";
    select.addEventListener("change", () => this._changed({ entity: select.value }));
    label.append(select);
    this.shadowRoot.append(label);

    const settings = element("details");
    settings.open = true;
    settings.append(element("summary", "", strings.editor.settings));

    const titleLabel = element("label", "", strings.editor.title);
    const titleInput = element("input");
    titleInput.type = "text";
    titleInput.value = this._config.title || "";
    titleInput.addEventListener("change", () => this._changed({ title: titleInput.value }));
    titleLabel.append(titleInput);
    settings.append(titleLabel);

    const checks = [
      ["show_address", strings.editor.address],
      ["show_status_strip", strings.editor.strip],
      ["show_power", strings.editor.power],
      ["show_status_time", strings.editor.time],
    ];
    if (this.detailed) checks.push(["show_cable", strings.editor.cable]);
    for (const [key, caption] of checks) {
      const checkLabel = element("label", "check", caption);
      const input = element("input");
      input.type = "checkbox";
      input.checked = key === "show_status_strip" && this.chips
        ? this._config.show_status_strip === true : visible(this._config, key);
      input.addEventListener("change", () => this._changed({ [key]: input.checked }));
      checkLabel.prepend(input);
      settings.append(checkLabel);
    }

    const plugLabel = element("label", "", strings.editor.plugStyle);
    const plugSelect = element("select");
    for (const [value, caption] of [
      ["icon_text", strings.editor.iconText],
      ["icon_only", strings.editor.iconOnly],
    ]) {
      const option = element("option", "", caption);
      option.value = value;
      plugSelect.append(option);
    }
    plugSelect.value = this._config.plug_style || "icon_text";
    plugSelect.addEventListener("change", () => this._changed({ plug_style: plugSelect.value }));
    plugLabel.append(plugSelect);
    settings.append(plugLabel);

    const tapLabel = element("label", "", strings.editor.tap);
    const tapSelect = element("select");
    const actionOptions = [
      ["more-info", strings.editor.moreInfo],
      ["none", strings.editor.noAction],
      ["navigate", strings.editor.navigate],
    ];
    const currentAction = this._config.tap_action?.action || "more-info";
    if (!actionOptions.some(([value]) => value === currentAction)) {
      actionOptions.push([currentAction, currentAction]);
    }
    for (const [value, caption] of actionOptions) {
      const option = element("option", "", caption);
      option.value = value;
      tapSelect.append(option);
    }
    tapSelect.value = currentAction;
    tapSelect.addEventListener("change", () => {
      const tapAction = tapSelect.value === "navigate"
        ? { action: "navigate", navigation_path: this._config.tap_action?.navigation_path || "" }
        : { action: tapSelect.value };
      this._changed({ tap_action: tapAction });
    });
    tapLabel.append(tapSelect);
    settings.append(tapLabel);
    if (currentAction === "navigate") {
      const pathLabel = element("label", "", strings.editor.path);
      const pathInput = element("input");
      pathInput.type = "text";
      pathInput.value = this._config.tap_action?.navigation_path || "";
      pathInput.addEventListener("change", () => this._changed({
        tap_action: { action: "navigate", navigation_path: pathInput.value },
      }));
      pathLabel.append(pathInput);
      settings.append(pathLabel);
    }
    this.shadowRoot.append(settings);
  }
}

for (const [type, name] of CARD_TYPES) {
  const cardClass = type.includes("compact") ? ChargeStationMapCompactCard
    : type.includes("chips") ? ChargeStationMapChipsCard : ChargeStationMapDetailCard;
  if (!customElements.get(type)) customElements.define(type, cardClass);
  window.customCards = window.customCards || [];
  if (!window.customCards.some((card) => card.type === type)) {
    window.customCards.push({
      type,
      name,
      description: type.includes("compact")
        ? "Kompakte Stationsübersicht mit Steckertypen und allen Ladepunkten"
        : type.includes("chips")
          ? "Schlanke, antippbare Ladepunkt-Kacheln im Mushroom-Stil"
          : "Ladepunktfelder mit allen Anschlüssen und genauen Statuszeiten",
      preview: true,
      getEntitySuggestion: (hass, entityId) =>
        isStation(hass.states?.[entityId])
          ? { config: { type: `custom:${type}`, entity: entityId } }
          : null,
    });
  }
}
if (!customElements.get("charge-station-map-card-editor")) {
  customElements.define("charge-station-map-card-editor", ChargeStationMapCardEditor);
}
