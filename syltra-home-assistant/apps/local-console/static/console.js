/* SYLTRA local console (spec §28, guidelines §4 and §9.2, ADR-007).
 *
 * No framework, no build step, no CDN. Everything the console shows comes from
 * the Local API, which has already translated reason codes into the requested
 * locale — the console never translates a reason code itself, so the two can
 * never disagree.
 *
 * The console renders text as text. Values from the API go through
 * `textContent`, never `innerHTML`, so a device named by a household can never
 * become markup.
 *
 * Navigation is filtered by the caller's permissions, which the API reports at
 * `/v1/me`. Guidelines §3 is explicit that this is presentation only: hiding a
 * control is not authorization, and every endpoint re-checks scope and
 * permission on every request. A hidden item is a tidier console, not a
 * protected one.
 */

const API = "";
const state = {
  locale: localStorage.getItem("syltra.locale") || "en",
  homeId: "",
  token: localStorage.getItem("syltra.token") || "",
  dict: {},
  view: "overview",
  param: null,
  holdRefresh: false,
  me: null,
  /* The live feed's own state. `healthy` gates the fallback poll: while the
     socket is delivering, polling every 15 seconds would be pure duplication. */
  stream: {
    socket: null,
    cursor: 0,
    healthy: false,
    attempt: 0,
    retry: null,
    pending: null,
    lastMessageAt: 0,
  },
};

/* ── navigation (§4) ──
 *
 * The primary navigation is fixed by §4 and appears in that order. Each item
 * names the permission it needs and the renderer that fills it.
 *
 * `unavailable` marks an item the *platform* cannot serve yet — no backend
 * exists behind it. Those are rendered and visibly marked rather than hidden,
 * because a console that silently omits half its information architecture
 * looks finished when it is not (§20). Contrast that with `permission`, which
 * removes the item entirely: there the answer is "not for you", not "not yet".
 */
const NAV = [
  { id: "overview", icon: "◧", permission: "READ_HOME", render: renderOverview },
  { id: "properties", icon: "▣", permission: "READ_HOME", render: renderProperties,
    detail: renderPropertyDetail },
  { id: "rooms", icon: "◱", permission: "READ_HOME", render: renderRooms,
    detail: renderRoomDetail },
  { id: "devices", icon: "⌂", permission: "READ_HOME", render: renderDevices,
    detail: renderDeviceDetail },
  { id: "scenes", icon: "◇", permission: "READ_HOME", render: renderScenes },
  { id: "goals", icon: "◎", permission: "READ_HOME", render: renderGoals },
  { id: "automations", icon: "⟳", permission: "READ_HOME", render: renderAutomations },
  { id: "intelligence", icon: "✷", permission: "READ_HOME", render: renderIntelligence },
  { id: "risks", icon: "△", permission: "READ_HOME", render: renderRisks,
    detail: renderRiskDetail },
  { id: "energy", icon: "◔", permission: "READ_HOME", render: renderEnergy },
  { id: "installations", icon: "▤", permission: "READ_HOME", unavailable: true },
  { id: "users", icon: "◎", permission: "READ_HOME", render: renderUsers },
  { id: "audit", icon: "☰", permission: "READ_AUDIT", render: renderAudit },
  { id: "health", icon: "♡", permission: "READ_HOME", render: renderHealth },
  { id: "settings", icon: "⚙", permission: "READ_HOME", render: renderSettings },
];

function navItem(id) {
  return NAV.find((item) => item.id === id);
}

function may(permission) {
  return Boolean(state.me && state.me.permissions.includes(permission));
}

function visibleNav() {
  return NAV.filter((item) => may(item.permission));
}

/* ── i18n ── */

async function loadDictionary() {
  const response = await fetch("./i18n.json");
  state.dict = await response.json();
}

function t(key) {
  const table = state.dict[state.locale] || state.dict.en || {};
  return table[key] || key;
}

function applyLocale() {
  const dir = t("dir") === "rtl" ? "rtl" : "ltr";
  document.documentElement.lang = state.locale;
  document.documentElement.dir = dir;
  document.title = t("title");
  for (const node of document.querySelectorAll("[data-i18n]")) {
    node.textContent = t(node.dataset.i18n);
  }
  /* An aria-label is text a screen reader reads aloud, so it needs translating
     as much as anything visible. */
  for (const node of document.querySelectorAll("[data-i18n-aria-label]")) {
    node.setAttribute("aria-label", t(node.dataset.i18nAriaLabel));
  }
  localStorage.setItem("syltra.locale", state.locale);
}

/* ── appearance (§4: appearance lives in the account area) ── */

function applyAppearance(choice) {
  const root = document.documentElement;
  /* "system" means *remove* the override, not set a third theme: the theme
     files already answer prefers-color-scheme when no explicit choice is
     present. */
  if (choice === "system") root.removeAttribute("data-theme");
  else root.setAttribute("data-theme", choice);
  localStorage.setItem("syltra.appearance", choice);
}

/* ── API ── */

async function api(path, options = {}) {
  const separator = path.includes("?") ? "&" : "?";
  const response = await fetch(`${API}${path}${separator}locale=${state.locale}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      "Accept-Language": state.locale,
      ...(state.token ? { Authorization: `Bearer ${state.token}` } : {}),
      ...(options.headers || {}),
    },
  });
  if (response.status === 401) throw new ApiError("unauthorized", response.status);
  if (response.status === 403) throw new ApiError("forbidden", response.status);
  if (!response.ok) throw new ApiError("error", response.status);
  return response.json();
}

class ApiError extends Error {
  constructor(key, status) {
    super(t(key));
    this.key = key;
    this.status = status;
  }
}

/* Load several sources at once, tolerating the failure of any of them.
 *
 * §20 requires a partial-data state and says to preserve unaffected data: if
 * risk cases cannot be read, the rooms and devices that loaded fine should
 * still be shown, with the gap named. Promise.all would discard all of it. */
async function loadAll(sources) {
  const names = Object.keys(sources);
  const settled = await Promise.allSettled(names.map((name) => sources[name]));
  const data = {};
  const failed = [];
  settled.forEach((result, index) => {
    if (result.status === "fulfilled") data[names[index]] = result.value;
    else failed.push({ name: names[index], error: result.reason });
  });
  return { data, failed };
}

/* ── DOM helpers ── */

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

function reasonList(reasons) {
  const list = el("ul", "reasons");
  for (const reason of reasons || []) list.append(el("li", null, reason));
  return list;
}

function fact(label, value) {
  const node = el("div", "fact");
  node.append(el("span", "fact__label", label));
  const valueNode = el("span", "fact__value");
  if (value instanceof Node) valueNode.append(value);
  else valueNode.textContent = value === undefined || value === null ? "—" : String(value);
  node.append(valueNode);
  return node;
}

function definitions(pairs) {
  const list = el("dl", "detail-list");
  for (const [term, value] of pairs) {
    list.append(el("dt", null, term));
    const dd = el("dd");
    if (value instanceof Node) dd.append(value);
    else dd.textContent = value === undefined || value === null ? "—" : String(value);
    list.append(dd);
  }
  return list;
}

function badge(variant, label) {
  return el("span", `badge badge--${variant}`, label);
}

function link(href, className, text) {
  const node = el("a", className, text);
  node.href = href;
  return node;
}

function setStatus(message) {
  document.getElementById("status-line").textContent = message || "";
}

function when(value) {
  return value ? new Date(value).toLocaleString(state.locale) : "—";
}

function clock(value) {
  return value ? new Date(value).toLocaleTimeString(state.locale) : "—";
}

/* Ages are shown in the coarsest unit that is still honest. "3 hours ago" is
   more useful than "11,431 seconds ago", and no less true. */
function ago(seconds) {
  if (seconds === undefined || seconds === null) return "—";
  const value = Math.max(0, Math.round(seconds));
  if (value < 60) return t("ago_seconds").replace("{n}", value);
  if (value < 3600) return t("ago_minutes").replace("{n}", Math.round(value / 60));
  if (value < 86400) return t("ago_hours").replace("{n}", Math.round(value / 3600));
  return t("ago_days").replace("{n}", Math.round(value / 86400));
}

/* A span of time, not a point in the past. `ago` says "5 minutes ago", which
   is right for an age and nonsense after "Expires in" or "Uptime". */
function duration(seconds) {
  if (seconds === undefined || seconds === null) return "—";
  const value = Math.max(0, Math.round(seconds));
  if (value < 60) return t("duration_seconds").replace("{n}", value);
  if (value < 3600) return t("duration_minutes").replace("{n}", Math.round(value / 60));
  if (value < 86400) return t("duration_hours").replace("{n}", Math.round(value / 3600));
  return t("duration_days").replace("{n}", Math.round(value / 86400));
}

function secondsSince(iso) {
  if (!iso) return null;
  return (Date.now() - new Date(iso).getTime()) / 1000;
}

/* ── §20 notices ── */

/* Every notice explains what happened, names what is affected, and where it
   can, offers one recovery action. None of them says "something went wrong". */
function notice(variant, title, detail, meta, recovery) {
  const node = el("div", `notice notice--${variant}`);
  node.append(el("p", "notice__title", title));
  if (detail) node.append(el("p", "notice__detail", detail));
  if (meta) node.append(el("p", "notice__meta", meta));
  if (recovery) {
    const actions = el("div", "notice__actions");
    const button = el("button", "btn btn--secondary", t("retry"));
    button.type = "button";
    button.addEventListener("click", () => refresh());
    actions.append(button);
    node.append(actions);
  }
  return node;
}

function failureNotice(error, affected) {
  if (error && error.key === "forbidden") {
    return notice("denied", t("denied_title"), t("denied_detail").replace("{what}", affected));
  }
  if (error && error.key === "unauthorized") {
    return notice("denied", t("unauthorized"), t("unauthorized_detail"));
  }
  return notice(
    "failure",
    t("failure_title").replace("{what}", affected),
    t("failure_detail"),
    null,
    true,
  );
}

function emptyNotice(key) {
  return notice("partial", t(key), null, null, null);
}

/* A partial load is not a failure and not a success. Naming which parts are
   missing is the whole point — "some data could not be loaded" without saying
   which is the same as saying nothing. */
function partialNotice(failed) {
  if (!failed.length) return null;
  const names = failed.map((f) => t(`source_${f.name}`)).join(", ");
  return notice(
    "partial",
    t("partial_title"),
    t("partial_detail").replace("{what}", names),
    t("partial_meta").replace("{when}", clock(new Date().toISOString())),
    true,
  );
}

/* ── §14 device state ──
 *
 * Derived from the platform's own judgement, never from a threshold invented
 * here: the Digital Twin marks each reading KNOWN, STALE or UNKNOWN against
 * that capability's `freshness_seconds`, so a gas detector and a power meter
 * are held to their own standards rather than a shared guess.
 */
function deviceState(device) {
  const readings = Object.values(device.capabilities || {});
  if (device.available === false) return { state: "offline", age: secondsSince(device.last_seen) };
  if (!readings.length) return { state: "unknown", age: null };

  const statuses = readings.map((r) => r.status);
  const oldest = Math.max(...readings.map((r) => r.age_seconds || 0));
  if (statuses.every((s) => s === "STALE")) return { state: "stale", age: oldest };
  if (statuses.every((s) => s === "UNKNOWN")) return { state: "unknown", age: null };
  /* A device reporting some capabilities and not others is degraded, not
     healthy — and saying "online" would hide exactly the thing worth seeing. */
  if (statuses.some((s) => s !== "KNOWN")) return { state: "degraded", age: oldest };
  return { state: "online", age: oldest };
}

/* §14 display rules: OFFLINE shows last seen, STALE shows the age of the data,
   UNKNOWN gets an explanation rather than a blank. */
function deviceStateCell(device) {
  const { state: name, age } = deviceState(device);
  const label = badge(name, t(`state_${name}`));
  if (name === "online") return label;
  const wrap = el("span", "state-with-age");
  wrap.append(label);
  if (name === "offline") wrap.append(el("span", "state-age", `${t("last_seen")} ${ago(age)}`));
  else if (name === "unknown") wrap.append(el("span", "state-age", t("state_unknown_detail")));
  else wrap.append(el("span", "state-age", `${ago(age)}`));
  return wrap;
}

const DEVICE_ICONS = [
  ["safety.gas_alarm", "◉"],
  ["safety.smoke_alarm", "◉"],
  ["safety.water_leak", "◉"],
  ["climate.", "◈"],
  ["environment.temperature", "◑"],
  ["environment.humidity", "◒"],
  ["light.", "☀"],
  ["occupancy.", "◍"],
  ["energy.", "◎"],
  ["contact.", "▢"],
];

function deviceIcon(device) {
  const capabilities = Object.keys(device.capabilities || {});
  for (const [prefix, glyph] of DEVICE_ICONS) {
    if (capabilities.some((c) => c.startsWith(prefix))) return glyph;
  }
  return "◌";
}

function deviceLabel(device) {
  return device.name || device.device_id;
}

function primaryReading(device) {
  const entries = Object.entries(device.capabilities || {});
  if (!entries.length) return "—";
  /* The first capability the platform reports is the device's primary one;
     the twin already orders them that way. */
  const [, reading] = entries[0];
  if (reading.status !== "KNOWN") return "—";
  if (typeof reading.value === "boolean") return t(reading.value ? "yes" : "no");
  return withUnit(reading.value, reading.unit);
}

/* ── confidence (§13.4: never presented as certainty) ── */

function confidenceLevel(value) {
  if (value >= 0.85) return t("confidence_high");
  if (value >= 0.6) return t("confidence_moderate");
  return t("confidence_low");
}

function confidenceBar(value) {
  const node = el("div", "confidence");
  node.append(el("span", "confidence__level", confidenceLevel(value)));
  node.append(el("span", "confidence__value", value.toFixed(2)));
  const track = el("span", "confidence__track");
  const fill = el("span", "confidence__fill");
  fill.style.inlineSize = `${Math.round(value * 100)}%`;
  track.append(fill);
  node.append(track);
  return node;
}

/* ── shared loaders ── */

async function loadHomeView(sources) {
  const { data, failed } = await loadAll(sources);
  return { data, failed };
}

function roomsFromDevices(devices) {
  const rooms = new Map();
  for (const device of devices) {
    const id = device.room_id || "unassigned";
    if (!rooms.has(id)) rooms.set(id, []);
    rooms.get(id).push(device);
  }
  return rooms;
}

function readingIn(devices, capability) {
  for (const device of devices) {
    const reading = (device.capabilities || {})[capability];
    if (reading && reading.status === "KNOWN") return reading;
  }
  return null;
}

/* The API reports the bare symbol — "C", "%" — because that is the unit. The
   degree sign is typography, and belongs here rather than in the contract. */
const UNIT_DISPLAY = { C: "°C", F: "°F" };

function withUnit(value, unit) {
  if (!unit) return String(value);
  const symbol = UNIT_DISPLAY[unit] || unit;
  /* No space before a degree sign or a percent, one before everything else. */
  return symbol.startsWith("°") || symbol === "%" ? `${value}${symbol}` : `${value} ${symbol}`;
}

function formatReading(reading) {
  if (!reading) return null;
  return withUnit(reading.value, reading.unit);
}

/* ── 13.1 property status header ── */

function propertyHeader(homeId, data) {
  const node = el("div", "property-header");
  const identity = el("div", "property-header__identity");
  identity.append(el("h2", "property-header__name", homeId));
  /* The platform holds no display name for a property, so the heading already
     *is* the identifier. Repeating it underneath said the same thing twice. */
  if (may("READ_DIAGNOSTICS")) {
    identity.append(el("span", "type-caption muted", t("identifier_note")));
  }
  node.append(identity);

  node.append(fact(t("local_time"), clock(new Date().toISOString())));

  const occupancy = (data.contexts && data.contexts.contexts) || [];
  const occupied = occupancy.find((c) => c.context_type === "HOME_OCCUPIED");
  const empty = occupancy.find((c) => c.context_type === "HOME_EMPTY");
  node.append(
    fact(
      t("occupancy"),
      occupied ? t("occupied") : empty ? t("empty_home") : t("state_unknown"),
    ),
  );

  const hubOk =
    data.status && Object.values(data.status.components || {}).every((c) => c === "ok");
  node.append(
    fact(
      t("hub"),
      data.status ? badge(hubOk ? "online" : "degraded", t(hubOk ? "state_online" : "state_degraded"))
        : badge("unknown", t("state_unknown")),
    ),
  );

  /* §4.2: no cloud dependency for local control. Saying so plainly is more
     useful than a connectivity dot, because it is the product's promise. */
  node.append(fact(t("cloud"), badge("offline", t("local_only"))));

  const cases = (data.risks && data.risks.cases) || [];
  const confirmed = cases.filter((c) => !c.advisory).length;
  node.append(
    fact(
      t("active_risks"),
      data.risks
        ? confirmed
          ? badge("confirmed", String(cases.length))
          : cases.length
            ? badge("advisory", String(cases.length))
            : String(0)
        : badge("unknown", t("state_unknown")),
    ),
  );

  node.append(fact(t("updated"), clock(new Date().toISOString())));
  return node;
}

/* ── §17.2 Overview ──
 *
 * The order is the guidelines': risk first, then property status, then health,
 * then context, then what needs a decision, then history. §17.2 also says not
 * to fill it with decorative KPIs, so nothing here is a number for its own
 * sake — every tile is something a person would act on.
 */
async function renderOverview(host) {
  const home = state.homeId;
  const { data, failed } = await loadHomeView({
    status: api("/v1/system/status"),
    devices: api(`/v1/homes/${home}/devices`),
    contexts: api(`/v1/homes/${home}/contexts/current`),
    risks: api(`/v1/homes/${home}/risks`),
    recommendations: api(`/v1/homes/${home}/recommendations`),
    actions: api(`/v1/homes/${home}/actions`),
  });

  const partial = partialNotice(failed);
  if (partial) host.append(partial);

  host.append(propertyHeader(home, data));

  if (data.devices) {
    const devices = data.devices.items || [];
    const states = devices.map((d) => deviceState(d).state);
    const attention = states.filter((s) => s !== "online").length;
    const metrics = el("div", "metric-row");
    metrics.append(metricTile(t("devices"), devices.length, t("devices_total")));
    metrics.append(
      metricTile(
        t("needs_attention"),
        attention,
        attention ? t("devices_not_reporting") : t("devices_all_reporting"),
      ),
    );
    metrics.append(metricTile(t("rooms"), roomsFromDevices(devices).size, null));
    host.append(metrics);
  }

  host.append(el("h2", "type-section-title", t("active_contexts")));
  if (!data.contexts) host.append(failureNotice(errorFor(failed, "contexts"), t("source_contexts")));
  else host.append(contextList(data.contexts.contexts || []));

  host.append(el("h2", "type-section-title", t("needs_decision")));
  if (!data.recommendations) {
    host.append(failureNotice(errorFor(failed, "recommendations"), t("source_recommendations")));
  } else {
    const items = (data.recommendations.items || []).filter((r) => r.requires_user_approval);
    if (!items.length) host.append(emptyNotice("no_recommendations"));
    else host.append(recommendationList(items));
  }

  host.append(el("h2", "type-section-title", t("recent_actions")));
  if (!data.actions) host.append(failureNotice(errorFor(failed, "actions"), t("source_actions")));
  else host.append(actionTable((data.actions.items || []).slice(0, 5)));
}

function errorFor(failed, name) {
  const entry = failed.find((f) => f.name === name);
  return entry ? entry.error : null;
}

function metricTile(label, value, detail) {
  const node = el("article", "card");
  node.append(el("h3", "card__title", label));
  node.append(el("p", "type-metric-large numeric", value));
  if (detail) node.append(el("p", "type-caption muted", detail));
  return node;
}

/* ── §17.3 Properties ── */

async function renderProperties(host) {
  /* The property list is the caller's own scope. There is one property in this
     build; the list is real rather than a placeholder, and grows when the
     platform grows a multi-property model. */
  const homes = state.me.homes;
  if (!homes.length) {
    host.append(notice("denied", t("no_properties"), t("no_properties_detail")));
    return;
  }

  const rows = [];
  const unreadable = [];
  for (const home of homes) {
    const { data, failed } = await loadHomeView({
      status: api("/v1/system/status"),
      devices: api(`/v1/homes/${home}/devices`),
      risks: api(`/v1/homes/${home}/risks`),
    });
    /* A property whose data would not load is listed as unreadable rather than
       shown with zeroes. "0 devices, 0 risks" for a property nobody could
       reach reads as a quiet, healthy home. */
    if (failed.length) unreadable.push({ home, failed });

    const devices = (data.devices && data.devices.items) || [];
    const attention = devices.filter((d) => deviceState(d).state !== "online").length;
    const cases = (data.risks && data.risks.cases) || [];
    const hubOk =
      data.status && Object.values(data.status.components || {}).every((c) => c === "ok");
    rows.push([
      link(`#/properties/${home}`, "identifier", home),
      data.status
        ? badge(hubOk ? "online" : "degraded", t(hubOk ? "state_online" : "state_degraded"))
        : badge("unknown", t("state_unknown")),
      data.devices
        ? attention
          ? `${devices.length - attention}/${devices.length}`
          : String(devices.length)
        : "—",
      data.risks
        ? cases.length
          ? badge(cases.some((c) => !c.advisory) ? "confirmed" : "advisory", String(cases.length))
          : "0"
        : badge("unknown", t("state_unknown")),
      clock(new Date().toISOString()),
    ]);
  }

  if (unreadable.length) {
    host.append(
      notice(
        "partial",
        t("properties_partial"),
        t("properties_partial_detail").replace(
          "{what}",
          unreadable.map((entry) => entry.home).join(", "),
        ),
        null,
        true,
      ),
    );
  }

  /* §17.3 also lists city, energy summary and owner. The platform holds none
     of those, so the columns are absent rather than filled with placeholders. */
  host.append(
    scrollableTable(["property", "hub", "devices_reporting", "active_risks", "updated"], rows),
  );
  host.append(el("p", "type-caption muted", t("properties_note")));
}

async function renderPropertyDetail(host, homeId) {
  if (!state.me.homes.includes(homeId)) {
    host.append(notice("denied", t("denied_title"), t("denied_property")));
    return;
  }
  const { data, failed } = await loadHomeView({
    status: api("/v1/system/status"),
    devices: api(`/v1/homes/${homeId}/devices`),
    contexts: api(`/v1/homes/${homeId}/contexts/current`),
    risks: api(`/v1/homes/${homeId}/risks`),
    recommendations: api(`/v1/homes/${homeId}/recommendations`),
    actions: api(`/v1/homes/${homeId}/actions`),
  });

  const partial = partialNotice(failed);
  if (partial) host.append(partial);
  host.append(propertyHeader(homeId, data));

  const devices = (data.devices && data.devices.items) || [];

  host.append(el("h2", "type-section-title", t("nav_rooms")));
  host.append(roomCards(devices, data.contexts));

  host.append(el("h2", "type-section-title", t("devices_needing_attention")));
  const attention = devices.filter((d) => deviceState(d).state !== "online");
  if (!attention.length) host.append(emptyNotice("devices_all_reporting"));
  else host.append(deviceTable(attention));

  host.append(el("h2", "type-section-title", t("active_contexts")));
  host.append(contextList((data.contexts && data.contexts.contexts) || []));

  host.append(el("h2", "type-section-title", t("nav_intelligence")));
  const items = (data.recommendations && data.recommendations.items) || [];
  if (!items.length) host.append(emptyNotice("no_recommendations"));
  else host.append(recommendationList(items));

  host.append(el("h2", "type-section-title", t("recent_actions")));
  host.append(actionTable(((data.actions && data.actions.items) || []).slice(0, 10)));

  /* §17.4 also lists active automations and energy. Neither exists yet. */
  host.append(notice("partial", t("sections_not_yet"), t("sections_not_yet_detail")));
}

/* ── §17.5 Rooms and room detail ── */

function roomCards(devices, contextsBody) {
  const rooms = roomsFromDevices(devices);
  if (!rooms.size) return emptyNotice("no_rooms");
  const occupiedRooms = new Set(
    ((contextsBody && contextsBody.contexts) || [])
      .filter((c) => c.context_type === "ROOM_OCCUPIED" && c.scope)
      .map((c) => c.scope),
  );
  const grid = el("div", "card-grid");
  for (const [roomId, roomDevices] of [...rooms].sort()) {
    const card = link(`#/rooms/${roomId}`, "room-card");
    const head = el("div", "room-card__head");
    head.append(el("h3", "room-card__name", roomId));
    const worst = roomDevices.map((d) => deviceState(d).state);
    if (worst.includes("offline")) head.append(badge("offline", t("state_offline")));
    else if (worst.includes("stale")) head.append(badge("stale", t("state_stale")));
    else if (occupiedRooms.has(roomId)) head.append(badge("online", t("occupied")));
    card.append(head);

    /* §13.2: not every room metric. Temperature, humidity, lights — the three
       a person actually asks about from another room. */
    const metrics = el("div", "room-card__metrics");
    const temperature = formatReading(readingIn(roomDevices, "environment.temperature"));
    const humidity = formatReading(readingIn(roomDevices, "environment.humidity"));
    /* `light.power` is the boolean on/off capability. An earlier version read
       `light.on`, which is not a capability the platform defines — so the
       count was always zero and the card quietly claimed every room was
       dark. */
    const lightsOn = roomDevices.filter((d) => {
      const reading = (d.capabilities || {})["light.power"];
      return reading && reading.status === "KNOWN" && reading.value === true;
    }).length;
    metrics.append(fact(t("temperature"), temperature));
    if (humidity) metrics.append(fact(t("humidity"), humidity));
    metrics.append(fact(t("lights_on"), lightsOn));
    card.append(metrics);
    card.append(el("p", "type-caption muted", `${roomDevices.length} ${t("devices").toLowerCase()}`));
    grid.append(card);
  }
  return grid;
}

async function renderRooms(host) {
  const { data, failed } = await loadHomeView({
    devices: api(`/v1/homes/${state.homeId}/devices`),
    contexts: api(`/v1/homes/${state.homeId}/contexts/current`),
  });
  const partial = partialNotice(failed);
  if (partial) host.append(partial);
  if (!data.devices) {
    host.append(failureNotice(errorFor(failed, "devices"), t("source_devices")));
    return;
  }
  host.append(el("h2", "type-section-title", t("nav_rooms")));
  host.append(roomCards(data.devices.items || [], data.contexts));
}

async function renderRoomDetail(host, roomId) {
  const { data, failed } = await loadHomeView({
    devices: api(`/v1/homes/${state.homeId}/devices`),
    contexts: api(`/v1/homes/${state.homeId}/contexts/current`),
    risks: api(`/v1/homes/${state.homeId}/risks`),
  });
  const partial = partialNotice(failed);
  if (partial) host.append(partial);
  if (!data.devices) {
    host.append(failureNotice(errorFor(failed, "devices"), t("source_devices")));
    return;
  }
  const devices = (data.devices.items || []).filter((d) => (d.room_id || "unassigned") === roomId);
  if (!devices.length) {
    host.append(notice("partial", t("room_not_found"), t("room_not_found_detail")));
    return;
  }

  host.append(el("h2", "type-section-title", t("environment")));
  const environment = el("div", "metric-row");
  const temperature = formatReading(readingIn(devices, "environment.temperature"));
  const humidity = formatReading(readingIn(devices, "environment.humidity"));
  environment.append(metricTile(t("temperature"), temperature || "—", null));
  environment.append(metricTile(t("humidity"), humidity || "—", null));
  environment.append(metricTile(t("devices"), devices.length, null));
  host.append(environment);

  host.append(el("h2", "type-section-title", t("nav_devices")));
  host.append(deviceTable(devices));

  host.append(el("h2", "type-section-title", t("active_contexts")));
  const roomContexts = ((data.contexts && data.contexts.contexts) || []).filter(
    (c) => c.scope === roomId || c.scope === "home",
  );
  host.append(contextList(roomContexts));

  host.append(el("h2", "type-section-title", t("problems")));
  const problems = ((data.risks && data.risks.cases) || []).filter((c) => c.room_id === roomId);
  const notReporting = devices.filter((d) => deviceState(d).state !== "online");
  if (!problems.length && !notReporting.length) host.append(emptyNotice("no_problems"));
  else {
    if (problems.length) host.append(riskList(problems));
    if (notReporting.length) host.append(deviceTable(notReporting));
  }
}

/* ── §17.6 Devices ── */

function deviceTable(devices) {
  const rows = devices.map((device) => {
    const name = el("span", "device-name");
    const icon = el("span", "device-type", deviceIcon(device));
    icon.setAttribute("aria-hidden", "true");
    name.append(icon);
    name.append(link(`#/devices/${device.device_id}`, null, deviceLabel(device)));
    return [
      name,
      device.room_id || "—",
      primaryReading(device),
      deviceStateCell(device),
      manualControl(device),
    ];
  });
  return scrollableTable(["device", "room", "state", "availability", "control"], rows);
}

/* ── manual control (§0 rule 5) ──

   The console could approve a recommendation and could not switch anything on.
   Manual override was honoured by the policy chain and produced by nothing, so
   the rule held for a physical switch — which Home Assistant reports — and had
   no path through this screen at all.

   The server says which capabilities this caller may operate, so a column that
   is empty for a lock is empty because the answer came back that way, not
   because the console decided. */

function manualControl(device) {
  const operable = Object.entries(device.capabilities || {}).filter(
    ([, reading]) => reading.operable && typeof reading.value === "boolean",
  );
  if (!operable.length) return el("span", "muted", "—");

  const wrapper = el("div", "row");
  for (const [capability, reading] of operable) {
    const on = reading.value === true;
    const button = el("button", "btn btn--secondary", on ? t("turn_off") : t("turn_on"));
    button.type = "button";
    button.addEventListener("click", async () => {
      button.setAttribute("aria-busy", "true");
      try {
        await api(`/v1/homes/${state.homeId}/devices/${device.device_id}/${capability}`, {
          method: "POST",
          body: JSON.stringify({ value: !on }),
        });
        await refresh();
      } catch (error) {
        /* Shown rather than swallowed: a button that silently does nothing is
           worse than one that says it was refused. */
        button.after(failureNotice(error, t("source_devices")));
      } finally {
        button.removeAttribute("aria-busy");
      }
    });
    wrapper.append(button);
  }
  return wrapper;
}

async function renderDevices(host) {
  const { data, failed } = await loadHomeView({
    devices: api(`/v1/homes/${state.homeId}/devices`),
  });
  if (!data.devices) {
    host.append(failureNotice(errorFor(failed, "devices"), t("source_devices")));
    return;
  }
  const devices = data.devices.items || [];
  if (!devices.length) {
    host.append(emptyNotice("no_devices"));
    return;
  }

  /* §17.6 lists nine filters. Four are backed by data the platform reports;
     protocol, battery, firmware, risk and installation status are not, so they
     are absent rather than present and inert. */
  const filters = el("div", "filters");
  const rooms = [...new Set(devices.map((d) => d.room_id || "unassigned"))].sort();
  const roomFilter = selectFilter("device-room", t("room"), t("all_rooms"), rooms);
  const stateFilter = selectFilter("device-state", t("availability"), t("all_states"), [
    "online",
    "degraded",
    "stale",
    "offline",
    "unknown",
  ], (value) => t(`state_${value}`));
  filters.append(roomFilter.node, stateFilter.node);
  const summary = el("span", "filter-summary");
  filters.append(summary);
  host.append(filters);

  const results = el("div");
  host.append(results);

  function apply() {
    const room = roomFilter.select.value;
    const wanted = stateFilter.select.value;
    const shown = devices.filter(
      (d) =>
        (room === "" || (d.room_id || "unassigned") === room) &&
        (wanted === "" || deviceState(d).state === wanted),
    );
    summary.textContent = t("filter_summary")
      .replace("{shown}", shown.length)
      .replace("{total}", devices.length);
    results.replaceChildren();
    /* §20 distinguishes an empty first-use state from an empty *filtered*
       state. They need different words: one means the home has no devices, the
       other means these filters match none of them. */
    if (!shown.length) results.append(notice("partial", t("no_matches"), t("no_matches_detail")));
    else results.append(deviceTable(shown));
  }

  roomFilter.select.addEventListener("change", apply);
  stateFilter.select.addEventListener("change", apply);
  apply();
}

function selectFilter(id, label, allLabel, values, format) {
  const node = el("div", "filter");
  const labelNode = el("label", "filter__label", label);
  labelNode.htmlFor = id;
  const select = el("select", "select");
  select.id = id;
  const all = el("option", null, allLabel);
  all.value = "";
  select.append(all);
  for (const value of values) {
    const option = el("option", null, format ? format(value) : value);
    option.value = value;
    select.append(option);
  }
  node.append(labelNode, select);
  return { node, select };
}

/* ── §17.7 Device detail ── */

async function renderDeviceDetail(host, deviceId) {
  const { data, failed } = await loadHomeView({
    devices: api(`/v1/homes/${state.homeId}/devices`),
  });
  if (!data.devices) {
    host.append(failureNotice(errorFor(failed, "devices"), t("source_devices")));
    return;
  }
  const device = (data.devices.items || []).find((d) => d.device_id === deviceId);
  if (!device) {
    host.append(notice("partial", t("device_not_found"), t("device_not_found_detail")));
    return;
  }

  const { state: stateName, age } = deviceState(device);
  if (stateName === "stale" || stateName === "offline" || stateName === "degraded") {
    /* §20: do not show a normal state when the data is unavailable. The banner
       says the readings below are the last received, not the current ones. */
    host.append(
      notice(
        stateName === "offline" ? "offline" : "stale",
        t(`detail_${stateName}_title`),
        t(`detail_${stateName}_detail`),
        `${t("last_seen")} ${ago(age)}`,
        true,
      ),
    );
  }

  host.append(el("h2", "type-section-title", t("current_state")));
  host.append(
    definitions([
      [t("room"), device.room_id ? link(`#/rooms/${device.room_id}`, null, device.room_id) : "—"],
      [t("property"), state.homeId],
      [t("availability"), deviceStateCell(device)],
      [t("last_update"), when(device.last_seen)],
    ]),
  );

  host.append(el("h2", "type-section-title", t("capabilities")));
  const rows = Object.entries(device.capabilities || {}).map(([capability, reading]) => [
    may("READ_DIAGNOSTICS") ? el("span", "identifier", capability) : friendlyCapability(capability),
    reading.status === "KNOWN" ? withUnit(reading.value, reading.unit) : "—",
    badge(reading.status === "KNOWN" ? "online" : reading.status === "STALE" ? "stale" : "unknown",
      t(`state_${reading.status.toLowerCase()}`)),
    ago(reading.age_seconds),
  ]);
  if (!rows.length) host.append(emptyNotice("no_capabilities"));
  else host.append(scrollableTable(["capability", "value", "status", "age"], rows));

  /* §17.7: "hide low-level identifiers from ordinary users and expose them to
     authorized technicians". The permission, not the role name, decides. */
  if (may("READ_DIAGNOSTICS")) {
    const diagnostics = el("div", "diagnostics");
    diagnostics.append(el("p", "diagnostics__label", t("diagnostics_label")));
    diagnostics.append(
      definitions([
        [t("device_id"), el("span", "identifier", device.device_id)],
        [t("room_id"), el("span", "identifier", device.room_id || "—")],
        [t("last_seen"), el("span", "identifier", device.last_seen || "—")],
        [
          t("capabilities"),
          el("span", "identifier", Object.keys(device.capabilities || {}).join(", ") || "—"),
        ],
      ]),
    );
    host.append(diagnostics);
  }

  /* Controls, firmware, battery, signal, event history and maintenance are all
     §17.7 sections the platform does not yet expose. Saying so is better than
     an empty panel that looks like a device with nothing to report. */
  host.append(notice("partial", t("sections_not_yet"), t("device_sections_not_yet")));
}

function friendlyCapability(capability) {
  const key = `capability_${capability.replace(/\./g, "_")}`;
  const label = t(key);
  return label === key ? capability.split(".").pop().replace(/_/g, " ") : label;
}

/* ── contexts, recommendations, risks, actions ── */

function contextList(contexts) {
  if (!contexts.length) return emptyNotice("no_contexts");
  const grid = el("div", "card-grid");
  for (const context of contexts) {
    const node = el("div", "context-card");
    const stale = context.seconds_until_expiry !== undefined && context.seconds_until_expiry <= 0;
    if (stale) node.dataset.stale = "true";
    node.append(el("h3", "card__title", t(`context_${context.context_type}`)));
    node.append(confidenceBar(context.confidence));
    const meta = el("p", "muted");
    meta.textContent = `${t("scope")}: ${context.scope} · ${t("evidence")}: ${(context.evidence || []).length}`;
    node.append(meta);
    if (context.advisory_only) node.append(badge("advisory", t("advisory")));
    if (stale) node.append(badge("stale", t("state_stale")));
    else if (context.seconds_until_expiry !== undefined) {
      node.append(el("p", "expiry", `${t("expires_in")} ${duration(context.seconds_until_expiry)}`));
    }
    node.append(reasonList(context.reasons));
    grid.append(node);
  }
  return grid;
}

function recommendationList(items) {
  const grid = el("div", "card-grid");
  for (const item of items) grid.append(recommendationCard(item));
  return grid;
}

/* §13.4 recommendation card.
 *
 * The card's job is to make a proposal reviewable: what is proposed, why, how
 * sure the platform is, what policy decided, when it expires, and what a
 * person may do about it. §13.4 forbids presenting confidence as certainty and
 * forbids phrasing like "SILA knows" when the state is inferred — so the
 * language here is always proposing, never reporting.
 */
function recommendationCard(item) {
  const node = el("div", "recommendation");
  node.append(el("h3", "recommendation__proposal", proposalText(item)));
  node.append(confidenceBar(item.confidence));

  const targets = el("div", "recommendation__targets");
  /* §19.2 and §15: shadow, advisory and approved are three different claims
     and none of them means the platform has done anything. */
  if (item.shadow) targets.append(badge("shadow", t("shadow")));
  if (item.target && item.target.device_id) {
    targets.append(
      link(`#/devices/${item.target.device_id}`, "badge badge--unknown", item.target.device_id),
    );
  }
  node.append(targets);

  node.append(el("h4", "muted", t("why")));
  node.append(reasonList(item.reasons));

  node.append(policyPanel(item));

  node.append(
    el("p", "expiry",
      `${t("suggested")} ${clock(item.created_at)} · ${t("expires")} ${clock(item.expires_at)}`),
  );
  if (item.model) {
    /* §17.9: no raw model internals for household users. The name and version
       are provenance, not internals — but they are only useful to someone who
       can act on them, so they stay behind the diagnostics permission. */
    if (may("READ_DIAGNOSTICS")) {
      node.append(el("p", "type-caption identifier", `${item.model.name}@${item.model.version}`));
    } else {
      node.append(el("p", "type-caption muted", t("from_learned_pattern")));
    }
  }

  node.append(feedbackActions(item));
  return node;
}

/* §21 and the UI-3 acceptance criterion "SILA cannot bypass approval or policy
 * UI": the decision policy reached is shown on the card, with its reason and
 * its safety class, whether or not it permits anything.
 *
 * A shadow prediction has no decision, and saying so is the point: there is
 * nothing to approve because nothing was proposed for action. */
function policyPanel(item) {
  if (item.shadow) {
    return notice("partial", t("policy_shadow_title"), t("policy_shadow_detail"));
  }
  const policy = item.policy;
  if (!policy) {
    return notice("failure", t("policy_missing_title"), t("policy_missing_detail"));
  }
  const variant =
    policy.decision === "ALLOW"
      ? "partial"
      : policy.decision === "REQUIRE_USER_APPROVAL"
        ? "stale"
        : "denied";
  const panel = notice(
    variant,
    `${t("policy_decided")}: ${t(`policy_${policy.decision}`)}`,
    (policy.reasons || []).join(". "),
    `${t("safety_class")}: ${t(`class_${policy.safety_class}`)}`,
  );
  return panel;
}

/* §13.4 lists six responses. They are not all the same kind of thing:
 * approve and reject move a policy decision, the rest are feedback the models
 * learn from. Both go to the API; neither is applied locally. */
const FEEDBACK_KINDS = ["NOT_NOW", "MODIFY", "NEVER_REPEAT"];

function feedbackActions(item) {
  const actions = el("div", "recommendation__actions");

  /* Approve and reject exist only where policy asked for a person. Rendering
     them against a DENY would invite a click that cannot succeed, and rendering
     them for a shadow prediction would be the bypass §19.2 forbids. */
  const awaiting =
    !item.shadow && item.policy && item.policy.decision === "REQUIRE_USER_APPROVAL";
  if (awaiting && may("APPROVE_RECOMMENDATION")) {
    actions.append(decisionButton(item, "approve", "btn btn--primary"));
    actions.append(decisionButton(item, "reject", "btn btn--secondary"));
  } else if (awaiting) {
    actions.append(el("p", "muted", t("approval_needs_permission")));
  }

  /* Feedback is how a household teaches the models, and it is open to anyone
     who can see the home — a person who may not approve an action can still
     say it was a bad idea. */
  if (!item.shadow) {
    for (const kind of FEEDBACK_KINDS) {
      actions.append(feedbackButton(item, kind));
    }
  }
  return actions;
}

function feedbackButton(item, kind) {
  const button = el("button", "btn btn--ghost", t(`feedback_${kind}`));
  button.type = "button";
  button.addEventListener("click", async () => {
    button.setAttribute("aria-busy", "true");
    try {
      await api(`/v1/homes/${state.homeId}/recommendations/${item.recommendation_id}/feedback`, {
        method: "POST",
        body: JSON.stringify({ kind }),
      });
      await refresh();
      setStatus(t(`feedback_recorded_${kind}`));
    } catch (error) {
      setStatus(error.message);
    } finally {
      button.removeAttribute("aria-busy");
    }
  });
  return button;
}

/* Plain language, and never "SILA knows" (§13.4, §23): the platform is
   proposing, not reporting. */
function proposalText(item) {
  const target = item.target || {};
  const key = `proposal_${item.recommendation_type.replace(/\./g, "_")}`;
  const template = t(key);
  if (template !== key) {
    return template
      .replace("{value}", item.proposed_value)
      .replace("{device}", target.device_id || "")
      .replace("{room}", target.room_id || target.device_id || "");
  }
  return `${item.recommendation_type}: ${item.proposed_value}`;
}

function decisionButton(item, decision, className) {
  const button = el("button", className, t(decision));
  button.type = "button";
  button.addEventListener("click", async () => {
    button.setAttribute("aria-busy", "true");
    try {
      const result = await api(
        `/v1/homes/${state.homeId}/recommendations/${item.recommendation_id}/${decision}`,
        { method: "POST", body: JSON.stringify({}) },
      );
      /* Report what policy actually decided, not what was clicked: an approval
         that policy turned into something other than ALLOW is exactly the case
         a person needs told about.
         After the refresh, not before — `refresh` clears the status line, so
         setting it first meant the confirmation flashed and vanished. */
      await refresh();
      setStatus(`${t("policy_decided")}: ${t(`policy_${result.decision}`)}`);
    } catch (error) {
      setStatus(error.message);
    } finally {
      button.removeAttribute("aria-busy");
    }
  });
  return button;
}

function riskList(cases) {
  const grid = el("div", "card-grid");
  for (const item of cases) {
    const node = el("div", "risk-card");
    if (item.advisory) node.dataset.advisory = "true";
    else node.dataset.confirmed = "true";
    const heading = el("h3", "card__title");
    heading.append(
      link(`#/risks/${item.case_id}`, null, `${t(`risk_${item.category}`)} — ${item.room_id || t("home")}`),
    );
    node.append(heading);
    node.append(
      badge(item.advisory ? "advisory" : "confirmed", t(item.advisory ? "advisory" : "confirmed")),
    );
    node.append(el("p", "muted", `${t("severity")}: ${t(`severity_${item.severity}`)}`));
    if (item.advisory) node.append(el("p", "muted", t("advisory_explanation")));
    if (item.confirmed_by) {
      node.append(el("p", "muted", t("confirmed_explanation")));
      node.append(el("p", "type-caption identifier", item.confirmed_by));
    }
    node.append(el("h4", "muted", t("why")));
    node.append(reasonList(item.reasons));
    node.append(el("p", "expiry", `${t("opened")} ${when(item.opened_at)}`));
    grid.append(node);
  }
  return grid;
}

/* §17.10 fixes the Risk Centre's order, and the order is the safety argument:
 * a confirmed hazard is never below an advisory watch, however recent the
 * watch is. Sorting by time would bury the thing that matters. */
const RISK_STATE_ORDER = ["CONFIRMED", "PRE_ALERT", "WATCH", "RECOVERY", "CLOSED"];

function riskRank(item) {
  const index = RISK_STATE_ORDER.indexOf(item.state);
  return index < 0 ? RISK_STATE_ORDER.length : index;
}

async function renderRisks(host) {
  const { data, failed } = await loadHomeView({
    risks: api(`/v1/homes/${state.homeId}/risks`),
  });
  if (!data.risks) {
    host.append(failureNotice(errorFor(failed, "risks"), t("source_risks")));
    return;
  }
  const cases = data.risks.cases || [];
  if (!cases.length) {
    /* §20: never show a normal state when the data is unavailable — but this
       *is* the data, and it says there is nothing open. */
    host.append(emptyNotice("no_risks"));
    return;
  }

  const ordered = [...cases].sort(
    (a, b) => riskRank(a) - riskRank(b) || new Date(b.opened_at) - new Date(a.opened_at),
  );
  for (const stateName of RISK_STATE_ORDER) {
    const group = ordered.filter((c) => c.state === stateName);
    if (!group.length) continue;
    host.append(el("h2", "type-section-title", t(`risk_state_${stateName}`)));
    host.append(riskList(group));
  }
  const other = ordered.filter((c) => !RISK_STATE_ORDER.includes(c.state));
  if (other.length) {
    host.append(el("h2", "type-section-title", t("risk_state_other")));
    host.append(riskList(other));
  }
}

function actionTable(items) {
  if (!items.length) return emptyNotice("no_actions");
  const rows = items.map((item) => [
    when(item.completed_at),
    item.status,
    (item.reasons || []).join(", "),
  ]);
  return scrollableTable(["when", "status", "why"], rows);
}

/* ── §17.9 SILA Intelligence ── */

/* §16: "The UI must always show the active mode and what the mode permits."
 * The second half is the one that gets dropped — a mode name alone tells a
 * household nothing about whether the platform is about to do something. */
function learningModeBanner(mode) {
  const variant = mode === "SUSPENDED" || mode === "DISABLED" ? "denied" : "partial";
  return notice(
    variant,
    `${t("learning_mode")}: ${t(`mode_${mode}`)}`,
    t(`mode_${mode}_permits`),
    null,
  );
}

async function renderIntelligence(host) {
  const home = state.homeId;
  const { data, failed } = await loadHomeView({
    recommendations: api(`/v1/homes/${home}/recommendations`),
    models: api(`/v1/homes/${home}/models`),
    contexts: api(`/v1/homes/${home}/contexts/current`),
  });
  const partial = partialNotice(failed);
  if (partial) host.append(partial);

  // 1. current learning mode
  if (data.models) host.append(learningModeBanner(data.models.learning_mode));

  // 2. active recommendations
  host.append(el("h2", "type-section-title", t("active_recommendations")));
  if (!data.recommendations) {
    host.append(failureNotice(errorFor(failed, "recommendations"), t("source_recommendations")));
  } else {
    const items = data.recommendations.items || [];
    if (!items.length) host.append(emptyNotice("no_recommendations"));
    else host.append(recommendationList(items));
  }

  // 3. what SYLTRA has learned about this home
  host.append(el("h2", "type-section-title", t("learned_routines")));
  if (!data.contexts) {
    host.append(failureNotice(errorFor(failed, "contexts"), t("source_contexts")));
  } else {
    host.append(contextList(data.contexts.contexts || []));
  }

  if (!data.models) {
    host.append(failureNotice(errorFor(failed, "models"), t("source_models")));
    return;
  }
  const models = data.models.models || [];

  // 4. suspended models — §19.4: a model that lost the household's trust
  const suspended = models.filter((m) => m.status === "SUSPENDED");
  host.append(el("h2", "type-section-title", t("suspended_models")));
  if (!suspended.length) {
    host.append(emptyNotice("no_suspended_models"));
  } else {
    host.append(
      notice("denied", t("suspended_title"), t("suspended_detail")),
    );
    host.append(
      scrollableTable(
        ["model", "version", "status"],
        suspended.map((m) => [
          modelLabel(m),
          el("span", "identifier", m.version),
          badge("error", t("state_suspended")),
        ]),
      ),
    );
  }

  // 5. the technical view, for those who can act on it (§17.9)
  if (may("MANAGE_MODELS") || may("READ_DIAGNOSTICS")) {
    const technical = el("div", "diagnostics");
    technical.append(el("p", "diagnostics__label", t("models_technical_label")));
    if (!models.length) {
      technical.append(emptyNotice("no_models"));
      host.append(technical);
      return;
    }
    technical.append(
      scrollableTable(
        ["model", "version", "status", "metrics"],
        models.map((m) => [
          el("span", "identifier", m.name),
          el("span", "identifier", m.version),
          badge(
            m.status === "ACTIVE" ? "online" : m.status === "SUSPENDED" ? "error" : "unknown",
            m.status,
          ),
          Object.entries(m.evaluation_metrics || {})
            .slice(0, 3)
            .map(([key, value]) => `${key}=${value}`)
            .join(", "),
        ]),
      ),
    );
    host.append(technical);
  }

  // 6. privacy and learning controls (§17.9)
  const controls = el("div", "card readable-column");
  controls.append(el("h3", "card__title", t("learning_controls")));
  controls.append(el("p", "muted", t("learning_controls_detail")));
  controls.append(link("#/settings", "btn btn--secondary", t("nav_settings")));
  host.append(controls);
}

function modelLabel(model) {
  const key = `model_${model.name}`;
  const label = t(key);
  return label === key ? model.name : label;
}

/* ── §13.7 action timeline ── */

/* §13.7 names eight stages. The platform emits the ones it actually performs,
 * and this shows those — a stage the platform never reached is absent rather
 * than drawn as pending, which would claim progress that is not happening.
 *
 * Correlation ids are for authorized technicians (§13.7), so they follow the
 * same permission as every other low-level identifier.
 */
const TIMELINE_STAGES = {
  POLICY_DECISION_CREATED: "stage_policy",
  POLICY_DECISION_NOT_AUTHORIZING: "stage_policy_refused",
  POLICY_APPROVAL_GRANTED: "stage_approval",
  POLICY_APPROVAL_REJECTED: "stage_rejection",
  ACTION_REQUESTED: "stage_dispatch",
  ACTION_DEDUPLICATED: "stage_deduplicated",
  ACTION_COMPENSATED: "stage_compensated",
  ACTION_EXPIRED_BEFORE_DISPATCH: "stage_expired",
  ACTION_EXPIRED: "stage_expired",
  ACTION_CANCELLED_BY_MANUAL_OVERRIDE: "stage_override",
  MANUAL_OVERRIDE_DETECTED: "stage_override",
};

/* Manual control always wins, so an override is never just another row. */
const OVERRIDE_STAGES = new Set(["stage_override"]);

function stageOf(entry) {
  return TIMELINE_STAGES[String(entry.action || "")] || null;
}

function timeline(entries) {
  if (!entries.length) return emptyNotice("no_timeline");
  const list = el("div", "stack");
  /* The audit feed arrives newest first, which is right for a log and wrong
     for a timeline: §13.7's stages have a natural sequence, and reading
     "approved" above "policy decided" inverts cause and effect. */
  const ordered = [...entries].sort(
    (a, b) => new Date(a.occurred_at) - new Date(b.occurred_at),
  );
  for (const entry of ordered) {
    const stage = stageOf(entry);
    const node = el("div", "notice");
    /* A manual override is not a footnote in a list of automated steps. §21
       and the platform rule that manual control always wins mean it is marked
       as the thing that took precedence. */
    if (OVERRIDE_STAGES.has(stage)) node.className = "notice notice--stale";
    node.append(
      el("p", "notice__title", stage ? t(stage) : entry.action),
    );
    if (entry.reason || (entry.reasons || []).length) {
      node.append(el("p", "notice__detail", entry.reason || (entry.reasons || []).join(". ")));
    }
    const meta = el("p", "notice__meta");
    meta.textContent = `${when(entry.occurred_at)} · ${entry.actor || t("actor_platform")}`;
    node.append(meta);
    if (may("READ_DIAGNOSTICS") && entry.correlation_id) {
      node.append(el("p", "type-caption identifier", entry.correlation_id));
    }
    list.append(node);
  }
  return list;
}

/* ── §17.10 risk detail ── */

async function renderRiskDetail(host, caseId) {
  let detail;
  try {
    detail = await api(`/v1/homes/${state.homeId}/risks/${caseId}`);
  } catch (error) {
    /* 404 means no such case; 422 means the id in the URL is not even an id.
       Both are a bad link, and reporting either as "risk cases could not be
       loaded" would blame the service for a mistyped address — §20 asks for
       the actual reason, not the nearest generic one. */
    if (error.status === 404 || error.status === 422) {
      host.append(notice("partial", t("risk_not_found"), t("risk_not_found_detail")));
      return;
    }
    host.append(failureNotice(error, t("source_risks")));
    return;
  }

  host.append(riskList([detail]));

  host.append(el("h2", "type-section-title", t("evidence_heading")));
  const evidence = detail.evidence || [];
  if (!evidence.length) {
    host.append(emptyNotice("no_evidence"));
  } else {
    host.append(
      scrollableTable(
        ["what", "device", "value", "status"],
        evidence.map((item) => [
          may("READ_DIAGNOSTICS")
            ? el("span", "identifier", item.capability)
            : friendlyCapability(item.capability),
          item.device_id
            ? link(`#/devices/${item.device_id}`, null, item.device_id)
            : "—",
          String(item.value),
          badge(item.status === "KNOWN" ? "online" : "stale", t(`state_${String(item.status).toLowerCase()}`)),
        ]),
      ),
    );
  }

  /* §21: the response a confirmation authorises is described, never offered as
     a control. Nothing in this console commands an actuator, and a risk page
     is the last place to start. */
  if (!detail.advisory) {
    host.append(el("h2", "type-section-title", t("authorized_response")));
    host.append(responsePlan(detail));
  }

  if (may("READ_AUDIT")) {
    host.append(el("h2", "type-section-title", t("action_timeline")));
    try {
      const audit = await api(`/v1/audit?home_id=${state.homeId}`);
      host.append(timeline((audit.items || []).slice(0, 20)));
    } catch (error) {
      host.append(failureNotice(error, t("source_audit")));
    }
  }
}

/* What a confirmed hazard authorises, as the platform planned it.
 *
 * Three things, and the difference between them is the whole point:
 *   — what was **done** (the household was told; that operates nothing);
 *   — what is **prepared** (the valve is identified and verified, and the
 *     command is not sent);
 *   — what is **not this system's to do** (unlocking a door, sounding a siren),
 *     named rather than omitted so nobody reads a partial plan as a complete
 *     one.
 *
 * There is no control here. `dispatched` is reported, never toggled.
 */
function responsePlan(detail) {
  const plan = detail.response_plan;
  if (!plan) {
    return notice("failure", t("no_plan_title"), t("no_plan_detail"));
  }

  const wrap = el("div", "stack");
  wrap.append(
    notice(
      "partial",
      t("response_done"),
      (plan.notifications || []).map((n) => n.detail).join(". ") || t("response_none"),
      `${t("confirmed_by")}: ${detail.confirmed_by || "—"}`,
    ),
  );

  for (const step of plan.prepared || []) {
    wrap.append(
      notice(
        step.reachable ? "stale" : "failure",
        t(step.reachable ? "response_prepared" : "response_unreachable"),
        t("response_prepared_detail")
          .replace("{value}", String(step.intended_value))
          .replace("{device}", step.device_id || t("state_unknown")),
        step.detail,
      ),
    );
  }

  for (const item of plan.blocked || []) {
    wrap.append(
      notice("denied", t("response_blocked"), item.reason, t("response_blocked_detail")),
    );
  }

  /* Stated plainly, because "prepared" and "done" are one careless reading
     apart and the difference is whether a valve moved. */
  wrap.append(
    el(
      "p",
      "type-caption muted",
      t(plan.dispatched ? "response_dispatched" : "response_not_dispatched"),
    ),
  );
  return wrap;
}

/* ── §17.8 Automations ──
 *
 * The one thing here a household writes itself. §17.8 lists the fields a row
 * must carry and asks for a builder with version history and rollback; the
 * builder is **not** built, and the screen says so rather than implying a
 * missing button.
 *
 * What it does offer is the test mode §17.8 also asks for — a dry run that
 * evaluates every automation against the home as it is and changes nothing.
 * That is worth having on its own: "why didn't my automation run?" is the
 * question this screen exists to answer.
 */
/* ── the automation builder (§2.3, ADR-009) ──

   The whole point is that nobody writes anything. Four dropdowns and a time
   field produce the same typed graph the API accepts, because ADR-009 refused
   an interpreter and this must not smuggle one back in: there is no free-text
   field here, and every value comes from a list the server supplied.

   Three things the form has to teach without a manual, because a household
   meets them the first time an automation surprises them:

   - the capabilities it will not offer, and that the refusal is deliberate;
   - that touching a device by hand silences its automation;
   - that an automation cannot re-fire immediately, so "it did not run" is
     sometimes the guard rail rather than a fault.

   And a sentence, in the household's own language, before anything is saved.
   A person approving a standing instruction should be able to read it back. */

/* ── automations the platform noticed ──

   The bridge between the models and the rules. The adaptive engine has always
   been able to say "turn the light on now, you usually do"; it said it again
   every evening. This offers the rule instead, once.

   Two things the card must do that a recommendation card does not.

   It shows the evidence rather than a score: "you did this on 7 of the last 7
   days" is something a person can disagree with, and 0.83 is not.

   And it never enables anything. Accepting creates a normal automation, which
   arrives switched off like any other, and which the household can edit or
   delete. An action the model got wrong happens once; a rule it got wrong
   happens every day until somebody notices. */

function proposedAutomations(home, proposals) {
  const section = el("section", "card");
  section.append(el("h2", "type-section-title", t("proposals_title")));
  section.append(el("p", "muted", t("proposals_detail")));

  for (const proposal of proposals) {
    const item = el("div", "proposal");
    const when = `${String(proposal.at_hour).padStart(2, "0")}:${String(proposal.at_minute).padStart(2, "0")}`;
    item.append(
      el("p", "type-card-title",
        t("proposal_sentence")
          .replace("{time}", when)
          .replace("{device}", proposal.device_id)
          .replace("{what}", t(`cap_${proposal.capability.replace(".", "_")}`))),
    );
    /* The evidence, not the confidence. */
    item.append(
      el("p", "type-caption muted",
        t("proposal_evidence").replace("{days}", String(proposal.days_observed))),
    );
    item.append(badge("advisory", t("advisory")));

    const accept = el("button", "btn btn--primary", t("proposal_accept"));
    accept.type = "button";
    accept.addEventListener("click", async () => {
      accept.setAttribute("aria-busy", "true");
      try {
        await api(`/v1/homes/${home}/automations`, {
          method: "POST",
          body: JSON.stringify({
            name: t("proposal_default_name").replace("{time}", when),
            trigger: {
              kind: "AT_TIME",
              at_hour: proposal.at_hour,
              at_minute: proposal.at_minute,
              weekdays: proposal.weekdays,
            },
            actions: [
              {
                device_id: proposal.device_id,
                capability: proposal.capability,
                value: true,
              },
            ],
          }),
        });
        await refresh();
      } finally {
        accept.removeAttribute("aria-busy");
      }
    });
    item.append(accept);
    section.append(item);
  }
  return section;
}

function automationBuilder(home, options, onSaved) {
  const form = el("form", "card");
  form.noValidate = true;
  form.append(el("h2", "type-section-title", t("build_title")));
  form.append(el("p", "muted", t("build_detail")));

  const name = labelledInput("automation-name", t("automation_name"), "text");

  // ── when ──
  const when = selectField("automation-when", t("build_when"), [
    { value: "STATE_EQUALS", label: t("when_state_equals") },
    { value: "THRESHOLD_ABOVE", label: t("when_above") },
    { value: "THRESHOLD_BELOW", label: t("when_below") },
    { value: "CONTEXT_STARTED", label: t("when_context") },
    { value: "AT_TIME", label: t("when_at_time") },
  ]);

  const watch = selectField(
    "automation-watch",
    t("build_watch"),
    options.watch.map((entry) => ({
      value: `${entry.device_id}|${entry.capability}`,
      label: `${entry.device_id} — ${t(`cap_${entry.capability.replace(".", "_")}`)}`,
    })),
  );
  const triggerValue = labelledInput("automation-trigger-value", t("build_value"), "text");
  const context = selectField(
    "automation-context",
    t("build_context"),
    options.context_types.map((value) => ({ value, label: t(`context_${value.toLowerCase()}`) })),
  );
  const hour = labelledInput("automation-hour", t("build_hour"), "number");
  hour.input.min = "0";
  hour.input.max = "23";
  const minute = labelledInput("automation-minute", t("build_minute"), "number");
  minute.input.min = "0";
  minute.input.max = "59";

  // ── then ──
  const act = selectField(
    "automation-act",
    t("build_then"),
    options.act_on.map((entry) => ({
      value: `${entry.device_id}|${entry.capability}`,
      label: `${entry.device_id} — ${t(`cap_${entry.capability.replace(".", "_")}`)}`,
    })),
  );
  const actionValue = labelledInput("automation-action-value", t("build_action_value"), "text");

  const preview = el("p", "notice notice--partial");
  const submit = el("button", "btn btn--primary", t("build_submit"));
  submit.type = "submit";
  const outcome = el("div");

  form.append(
    name.node, when.node, watch.node, triggerValue.node, context.node,
    hour.node, minute.node, act.node, actionValue.node, preview, submit, outcome,
  );

  /* Only the fields the chosen trigger uses. A form that shows every field for
     every trigger asks a person to work out which ones matter. */
  function showRelevantFields() {
    const kind = when.select.value;
    watch.node.hidden = kind === "CONTEXT_STARTED" || kind === "AT_TIME";
    triggerValue.node.hidden = kind !== "STATE_EQUALS" && !kind.startsWith("THRESHOLD");
    context.node.hidden = kind !== "CONTEXT_STARTED";
    hour.node.hidden = minute.node.hidden = kind !== "AT_TIME";
    preview.textContent = previewSentence();
  }

  function previewSentence() {
    const kind = when.select.value;
    const target = act.select.value.split("|");
    const actLabel = act.select.options[act.select.selectedIndex]?.text || "";
    let trigger = "";
    if (kind === "AT_TIME") {
      trigger = t("preview_at_time")
        .replace("{hour}", String(hour.input.value || 0).padStart(2, "0"))
        .replace("{minute}", String(minute.input.value || 0).padStart(2, "0"));
    } else if (kind === "CONTEXT_STARTED") {
      trigger = t("preview_context").replace(
        "{context}", context.select.options[context.select.selectedIndex]?.text || "",
      );
    } else {
      const watchLabel = watch.select.options[watch.select.selectedIndex]?.text || "";
      trigger = t(`preview_${kind.toLowerCase()}`)
        .replace("{what}", watchLabel)
        .replace("{value}", triggerValue.input.value || "…");
    }
    return t("preview_sentence")
      .replace("{trigger}", trigger)
      .replace("{action}", actLabel)
      .replace("{value}", actionValue.input.value || "…")
      .replace("{device}", target[0] || "");
  }

  for (const field of [when.select, watch.select, context.select, act.select]) {
    field.addEventListener("change", showRelevantFields);
  }
  for (const field of [triggerValue.input, actionValue.input, hour.input, minute.input]) {
    field.addEventListener("input", showRelevantFields);
  }
  showRelevantFields();

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    outcome.replaceChildren();
    submit.setAttribute("aria-busy", "true");
    try {
      await api(`/v1/homes/${home}/automations`, {
        method: "POST",
        body: JSON.stringify(buildPayload()),
      });
      await onSaved();
    } catch (error) {
      /* The server's refusal, in the household's language. ADR-009's rules are
         enforced there and explained here rather than duplicated. */
      outcome.append(failureNotice(error, t("source_automations")));
    } finally {
      submit.removeAttribute("aria-busy");
    }
  });

  function buildPayload() {
    const kind = when.select.value;
    const [watchDevice, watchCapability] = watch.select.value.split("|");
    const [actDevice, actCapability] = act.select.value.split("|");
    const trigger = { kind };
    if (kind === "AT_TIME") {
      trigger.at_hour = Number(hour.input.value || 0);
      trigger.at_minute = Number(minute.input.value || 0);
    } else if (kind === "CONTEXT_STARTED") {
      trigger.context_type = context.select.value;
    } else {
      trigger.device_id = watchDevice;
      trigger.capability = watchCapability;
      trigger.value = coerce(triggerValue.input.value);
    }
    return {
      name: name.input.value.trim() || t("automation_untitled"),
      trigger,
      actions: [
        {
          device_id: actDevice,
          capability: actCapability,
          value: coerce(actionValue.input.value),
        },
      ],
    };
  }

  return form;
}

/* Dropdowns carry typed values, so "true" from a select is a boolean and "23"
   is a number by the time it reaches a contract that checks types. */
function coerce(raw) {
  const value = String(raw).trim();
  if (value === "true") return true;
  if (value === "false") return false;
  if (value !== "" && !Number.isNaN(Number(value))) return Number(value);
  return value;
}

function selectField(id, label, options) {
  const node = el("div", "field");
  const element = el("label", null, label);
  element.htmlFor = id;
  const select = el("select", "select");
  select.id = id;
  for (const option of options) {
    const item = el("option", null, option.label);
    item.value = option.value;
    select.append(item);
  }
  node.append(element, select);
  return { node, select };
}

/* ── scenes ──

   A list somebody presses, so the button is the point and everything else is
   context for it. The answer after a press is per-device rather than "done":
   a household that pressed *leaving* is owed a plain answer about the door. */

async function renderScenes(host) {
  const home = state.homeId;
  const { data, failed } = await loadHomeView({ scenes: api(`/v1/homes/${home}/scenes`) });
  if (!data.scenes) {
    host.append(failureNotice(errorFor(failed, "scenes"), t("nav_scenes")));
    return;
  }
  const items = data.scenes.items || [];
  const outcome = el("div");
  host.append(outcome);

  if (!items.length) {
    host.append(notice("partial", t("no_scenes"), t("no_scenes_detail")));
    return;
  }

  host.append(
    scrollableTable(
      ["name", "what_it_does", "scene_last_pressed", "control"],
      items.map((scene) => {
        /* Held as a node rather than a string so the row can be corrected in
           place after a press. The alternative is re-reading the whole screen,
           which would wipe the answer the press just produced. */
        const pressed = el(
          "span",
          null,
          scene.last_activated_at ? when(scene.last_activated_at) : t("scene_never_pressed"),
        );
        return [scene.name, scene.summary, pressed, activateControl(home, scene, outcome, pressed)];
      }),
    ),
  );
}

function activateControl(home, scene, outcome, pressed) {
  const button = el("button", "btn btn--secondary", t("scene_activate"));
  button.type = "button";
  /* Disabled rather than hidden, with the reason beside it: a household should
     be able to see that a scene exists and that this account cannot press it. */
  if (!scene.activatable) {
    button.disabled = true;
    button.title = t("scene_not_yours");
    return button;
  }
  button.addEventListener("click", async () => {
    button.setAttribute("aria-busy", "true");
    outcome.replaceChildren();
    /* Held *before* the request, not after: applying a scene changes the house,
       the change arrives back on the stream within milliseconds, and a re-read
       triggered by it would wipe the per-device answer this press produced. */
    state.holdRefresh = true;
    try {
      const result = await api(`/v1/homes/${home}/scenes/${scene.scene_id}/activate`, {
        method: "POST",
      });
      pressed.textContent = when(new Date().toISOString());
      const missed = (result.steps || []).filter((step) => !step.verified);
      outcome.append(
        missed.length
          ? notice(
              "partial",
              t("scene_partly_title").replace("{name}", scene.name),
              missed
                .map((step) => `${step.device_id}: ${(step.reasons || []).join(", ")}`)
                .join(" · "),
            )
          : notice("partial", t("scene_done_title").replace("{name}", scene.name), scene.summary),
      );
    } catch (error) {
      outcome.append(failureNotice(error, t("nav_scenes")));
    } finally {
      button.removeAttribute("aria-busy");
    }
  });
  return button;
}

/* ── goals ──

   Read-only here, and the reading is the whole feature: a goal's worth is that
   somebody can look at it and be told plainly whether it holds — including
   "nothing is measuring this", which is the answer every other product in this
   category rounds off to a green tick. */

const GOAL_BADGES = {
  SATISFIED: "online",
  VIOLATED: "error",
  UNKNOWN: "unknown",
  HELD: "stale",
  STALLED: "degraded",
  OFF: "disabled",
};

async function renderGoals(host) {
  const home = state.homeId;
  const { data, failed } = await loadHomeView({ goals: api(`/v1/homes/${home}/goals`) });
  if (!data.goals) {
    host.append(failureNotice(errorFor(failed, "goals"), t("nav_goals")));
    return;
  }
  const items = data.goals.items || [];
  if (!items.length) {
    host.append(notice("partial", t("no_goals"), t("no_goals_detail")));
    return;
  }

  host.append(
    scrollableTable(
      ["name", "goal_statement", "goal_state", "goal_measured", "goal_last_corrected"],
      items.map((goal) => [
        goal.name,
        goal.summary,
        goalState(goal),
        goal.measured === null || goal.measured === undefined
          ? t("goal_nothing_measured")
          : `${goal.measured}${goal.measured_by ? ` · ${goal.measured_by}` : ""}`,
        goal.last_corrected_at ? when(goal.last_corrected_at) : t("goal_never_corrected"),
      ]),
    ),
  );
  host.append(notice("partial", t("goals_explained_title"), t("goals_explained_detail")));
}

function goalState(goal) {
  /* The state and its reason together, because "not holding" and "nothing is
     measuring this" are different facts and a colour cannot carry the
     difference (§8). */
  const wrapper = el("div", "goal-state");
  const heading = el("div", "row");
  heading.append(badge(GOAL_BADGES[goal.state] || "unknown", t(`goal_state_${goal.state}`)));
  wrapper.append(heading);
  /* Only where the reason says something the badge does not. "Holding ·
     Holding" is noise, and noise beside a status is how a reader learns to
     skip the whole column — but "unmeasured" and "paused by hand" carry a fact
     the word alone does not, and those are exactly the two a household needs. */
  if (["UNKNOWN", "HELD", "OFF", "STALLED"].includes(goal.state)) {
    heading.append(el("span", "muted", goal.reason));
  }
  /* What the house can see standing in the way — each with the device that
     reported it, because "a window is open" is advice and "the living room
     window is open" is something somebody can go and shut. */
  if ((goal.obstacles || []).length) {
    const seen = el("div", "goal-state__obstacles");
    for (const obstacle of goal.obstacles) {
      seen.append(badge("stale", `${obstacle.reason} · ${obstacle.device_id}`));
    }
    wrapper.append(seen);
  }
  return wrapper;
}

async function renderAutomations(host) {
  const home = state.homeId;
  const { data, failed } = await loadHomeView({
    automations: api(`/v1/homes/${home}/automations`),
    options: api(`/v1/homes/${home}/automations/options`),
    proposals: api(`/v1/homes/${home}/automations/proposals`),
  });
  if (!data.automations) {
    host.append(failureNotice(errorFor(failed, "automations"), t("source_automations")));
    return;
  }
  const items = data.automations.items || [];

  const header = el("div", "page-header__actions");
  const dryRun = el("button", "btn btn--secondary", t("test_run"));
  dryRun.type = "button";
  header.append(dryRun);
  host.append(header);

  const outcome = el("div");
  host.append(outcome);

  dryRun.addEventListener("click", async () => {
    dryRun.setAttribute("aria-busy", "true");
    outcome.replaceChildren();
    try {
      const result = await api(`/v1/homes/${home}/automations/dry-run`, {
        method: "POST",
        body: JSON.stringify({}),
      });
      outcome.append(dryRunResult(result));
      // Hold the view so the periodic refresh does not wipe the answer.
      state.holdRefresh = true;
    } catch (error) {
      outcome.append(failureNotice(error, t("source_automations")));
    } finally {
      dryRun.removeAttribute("aria-busy");
    }
  });

  if (data.proposals && (data.proposals.proposals || []).length) {
    host.append(proposedAutomations(home, data.proposals.proposals));
  }

  if (data.options) {
    host.append(automationBuilder(home, data.options, refresh));
    /* Said once, near the form, because a household meets these the first time
       an automation does not do what they expected. */
    host.append(
      notice("partial", t("build_rules_title"),
        t("build_rules_detail").replace(
          "{seconds}", String(data.options.minimum_rearm_seconds))),
    );
    if ((data.options.not_automatable || []).length) {
      const excluded = el("ul", "list");
      for (const entry of data.options.not_automatable) {
        excluded.append(el("li", null, `${entry.device_id} — ${entry.reason}`));
      }
      const section = el("section", "card");
      section.append(el("h2", "type-section-title", t("not_automatable_title")));
      section.append(el("p", "muted", t("not_automatable_detail")));
      section.append(excluded);
      host.append(section);
    }
  }

  if (!items.length) {
    host.append(notice("partial", t("no_automations"), t("no_automations_detail")));
  } else {
    host.append(
      scrollableTable(
        ["name", "what_it_does", "source", "safety_class", "enabled", "last_run"],
        items.map((item) => [
          item.name,
          item.summary,
          t(`automation_source_${item.source}`),
          t(`class_${item.safety_class}`),
          enabledControl(item),
          item.last_run ? when(item.last_run) : t("automation_never_run"),
        ]),
      ),
    );
  }

  /* §17.8 asks for a builder, version history and rollback. The builder is
     above; the other two are not built, and saying so beats an empty screen
     that reads as a product which forgot them. */
  /* What is still missing, now that the builder is not. Version history and
     rollback would let a household undo an edit rather than rebuild it. */
  host.append(notice("partial", t("no_history"), t("no_history_detail")));
}

/* Switching an automation off is a real change to what the home does, so it
   goes to the API and the row re-reads rather than toggling optimistically —
   a switch that shows "off" while the automation is still armed is worse than
   one that takes a moment. */
function enabledControl(item) {
  if (!may("MANAGE_AUTOMATIONS")) {
    return badge(item.enabled ? "online" : "offline", t(item.enabled ? "enabled" : "disabled_state"));
  }
  const button = el("button", "btn btn--ghost", t(item.enabled ? "turn_off" : "turn_on"));
  button.type = "button";
  button.addEventListener("click", async () => {
    button.setAttribute("aria-busy", "true");
    try {
      await api(`/v1/homes/${state.homeId}/automations/${item.automation_id}/enabled`, {
        method: "POST",
        body: JSON.stringify({ enabled: !item.enabled }),
      });
      state.holdRefresh = false;
      await refresh();
      setStatus(t(item.enabled ? "automation_turned_off" : "automation_turned_on"));
    } catch (error) {
      setStatus(error.message);
    } finally {
      button.removeAttribute("aria-busy");
    }
  });
  return button;
}

function dryRunResult(result) {
  const wrap = el("div", "stack");
  wrap.append(
    notice(
      "partial",
      t("test_run_title"),
      t("test_run_detail"),
      `${t("checked_at")} ${clock(result.evaluated_at)}`,
    ),
  );
  if (result.would_run.length) {
    wrap.append(
      scrollableTable(
        ["name", "target", "value", "why"],
        result.would_run.map((entry) => [
          entry.name,
          entry.device_id || "—",
          String(entry.value),
          (entry.reasons || []).join(". "),
        ]),
      ),
    );
  } else {
    wrap.append(emptyNotice("test_run_nothing"));
  }
  if (result.would_not_run.length) {
    wrap.append(el("h3", "type-card-title", t("test_run_skipped")));
    wrap.append(
      scrollableTable(
        ["automation", "why"],
        result.would_not_run.map((entry) => [
          entry.automation_id,
          (entry.reasons || []).join(". "),
        ]),
      ),
    );
  }
  return wrap;
}

/* ── §17.11 Energy ──
 *
 * What this screen shows is bounded by what the platform measures, and §17.11
 * is explicit: "Never fabricate cost, savings, carbon, or device-level
 * estimates." There is no time-series endpoint, so there is no consumption
 * over time, no baseline comparison and no trend — and rather than leave that
 * as a silent absence, the screen names it.
 *
 * What it can show is real: current power from the devices that meter it, how
 * much of the home that covers, how fresh those readings are, and whether the
 * anomaly model or a risk case has flagged anything.
 */
/* A device meters power if it reports a reading *in watts*. Deriving that from
 * the unit rather than from the capability name matters more than it looks:
 * `light.power` and `switch.power` are boolean on/off controls, and matching on
 * the word "power" summed `true` into a wattage total and claimed the home was
 * twice as well metered as it is. §17.11 forbids device-level estimates, and an
 * inflated coverage figure is worse than an omission — it makes an incomplete
 * number look complete. */
const POWER_UNIT = "W";

function powerReading(device) {
  for (const [capability, reading] of Object.entries(device.capabilities || {})) {
    if (reading && reading.unit === POWER_UNIT) return { capability, ...reading };
  }
  return null;
}

function meteredDevices(devices) {
  return devices.filter((device) => powerReading(device) !== null);
}

/* ── power over time (§27 criterion 9) ──

   The one thing this chart does differently: it does not join across a gap.

   An hour nothing reported in is drawn as a gap, because a line through it
   would be a claim about consumption nobody measured — the exact estimate
   §17.11 forbids. Bars rather than a line, so each hour stands on its own and
   an absent one is visibly absent rather than being a slightly longer segment.

   Bar height is the mean; a fainter mark shows the maximum, because a mean of
   800 W over an hour hides a compressor that pulled 2.4 kW for four minutes,
   and that spike is usually what somebody opened this screen to find. */

function powerOverTime(history) {
  const section = el("section", "card");
  section.append(el("h2", "type-section-title", t("power_over_time")));

  const buckets = history.buckets || [];
  if (!buckets.length) {
    section.append(
      notice(
        "partial",
        history.recording_since ? t("no_history_yet") : t("no_history_at_all"),
        history.recording_since ? t("no_history_yet_detail") : t("no_history_at_all_detail"),
      ),
    );
    return section;
  }

  const peak = Math.max(...buckets.map((b) => b.maximum));
  const chart = el("div", "chart chart--bars");
  chart.setAttribute("role", "img");
  /* The whole chart as one sentence, because a bar chart is invisible to a
     screen reader and a per-bar label would read as noise (§18). */
  chart.setAttribute(
    "aria-label",
    t("power_over_time_summary")
      .replace("{buckets}", String(buckets.length))
      .replace("{missing}", String((history.missing || []).length))
      .replace("{peak}", String(Math.round(peak))),
  );

  for (const bucket of buckets) {
    const column = el("div", "chart__column");
    const bar = el("div", "chart__bar");
    bar.style.height = `${Math.max(2, (bucket.watts / peak) * 100)}%`;
    /* Coverage, shown rather than hidden: an hour with two readings and an
       hour with twelve are not the same claim, and the fainter bar says so
       without a second axis. */
    if (bucket.coverage < 0.5) bar.dataset.sparse = "true";
    const spike = el("div", "chart__peak");
    spike.style.bottom = `${(bucket.maximum / peak) * 100}%`;
    column.append(spike, bar);
    column.title = `${when(bucket.start)} — ${Math.round(bucket.watts)} W`;
    chart.append(column);
  }
  section.append(chart);

  const missing = (history.missing || []).length;
  section.append(
    el("p", "type-caption muted",
      missing
        ? t("history_gaps").replace("{n}", String(missing))
        : t("history_complete")),
  );
  /* Said out loud rather than left to be inferred from a hole in the chart. */
  section.append(el("p", "type-caption muted", t("history_never_estimated")));
  return section;
}

async function renderEnergy(host) {
  const home = state.homeId;
  const { data, failed } = await loadHomeView({
    devices: api(`/v1/homes/${home}/devices`),
    risks: api(`/v1/homes/${home}/risks`),
    models: api(`/v1/homes/${home}/models`),
    history: api(`/v1/homes/${home}/energy/history?resolution=hour&hours=24`),
  });
  const partial = partialNotice(failed);
  if (partial) host.append(partial);

  if (!data.devices) {
    host.append(failureNotice(errorFor(failed, "devices"), t("source_devices")));
    return;
  }
  const devices = data.devices.items || [];
  const metered = meteredDevices(devices);

  if (!metered.length) {
    host.append(notice("partial", t("no_metering"), t("no_metering_detail")));
    return;
  }

  // Data completeness and freshness, before the numbers they qualify.
  host.append(dataQuality(devices, metered));

  // Current power. Numeric only: there is no history to draw.
  const live = metered
    .map((device) => ({ device, reading: powerReading(device) }))
    .filter((entry) => entry.reading && entry.reading.status === "KNOWN");
  const total = live.reduce((sum, entry) => sum + Number(entry.reading.value || 0), 0);

  if (data.history) host.append(powerOverTime(data.history));

  host.append(el("h2", "type-section-title", t("current_power")));
  const metrics = el("div", "metric-row");
  const totalTile = metricTile(t("current_power"), withUnit(Math.round(total), "W"), null);
  /* An accessible summary, because the tile is a number without a chart and a
     screen reader user gets no visual context to infer from (§18). */
  totalTile.append(
    el("p", "type-caption muted",
      t("current_power_summary")
        .replace("{n}", String(live.length))
        .replace("{total}", String(metered.length))),
  );
  metrics.append(totalTile);
  metrics.append(metricTile(t("metered_devices"), `${metered.length}/${devices.length}`, null));
  host.append(metrics);

  // Breakdown by device — "where available", never estimated for the rest.
  host.append(el("h2", "type-section-title", t("by_device")));
  host.append(
    scrollableTable(
      ["device", "room", "power", "status", "age"],
      metered.map((device) => {
        const reading = powerReading(device);
        return [
          link(`#/devices/${device.device_id}`, null, deviceLabel(device)),
          device.room_id || "—",
          reading.status === "KNOWN" ? withUnit(reading.value, reading.unit) : "—",
          badge(
            reading.status === "KNOWN" ? "online" : reading.status === "STALE" ? "stale" : "unknown",
            t(`state_${String(reading.status).toLowerCase()}`),
          ),
          ago(reading.age_seconds),
        ];
      }),
    ),
  );

  // Anomalies — from the model and from any electrical risk case.
  host.append(el("h2", "type-section-title", t("anomalies")));
  const electrical = ((data.risks && data.risks.cases) || []).filter(
    (item) => item.category === "ELECTRICAL",
  );
  const anomalyModel = ((data.models && data.models.models) || []).find(
    (model) => model.name === "energy_anomaly",
  );
  if (electrical.length) {
    host.append(riskList(electrical));
  } else if (!anomalyModel) {
    host.append(notice("partial", t("no_anomaly_model"), t("no_anomaly_model_detail")));
  } else if (anomalyModel.status === "SUSPENDED") {
    host.append(notice("denied", t("anomaly_model_suspended"), t("anomaly_model_suspended_detail")));
  } else {
    host.append(emptyNotice("no_anomalies"));
  }

  /* §17.11 asks for consumption over time, a baseline comparison and cost.
     None is computable from what the platform records, and the section says
     never to fabricate them — so the screen says what it cannot show. */
  host.append(
    notice("partial", t("energy_not_measured"), t("energy_not_measured_detail")),
  );
}

function dataQuality(devices, metered) {
  const node = el("div", "data-quality");
  const readings = metered.map(powerReading).filter(Boolean);
  const ages = readings.map((r) => r.age_seconds).filter((a) => a !== undefined && a !== null);
  const known = readings.filter((r) => r.status === "KNOWN").length;

  node.append(fact(t("metered"), `${metered.length} ${t("of")} ${devices.length}`));
  node.append(fact(t("reporting_now"), `${known} ${t("of")} ${readings.length}`));
  node.append(fact(t("freshest"), ages.length ? ago(Math.min(...ages)) : "—"));
  node.append(fact(t("oldest"), ages.length ? ago(Math.max(...ages)) : "—"));

  const bar = el("span", "coverage-bar");
  const fill = el("span", "coverage-bar__fill");
  const coverage = devices.length ? Math.round((metered.length / devices.length) * 100) : 0;
  fill.style.inlineSize = `${coverage}%`;
  bar.append(fill);
  bar.setAttribute("role", "img");
  bar.setAttribute("aria-label", t("coverage_label").replace("{n}", String(coverage)));
  node.append(bar);
  return node;
}

/* ── §17.14 Audit Trail ──
 *
 * §17.14 lists ten fields. The platform records eight of them; role and
 * correlation id are not written at the time of the event, and the screen says
 * so rather than leaving two columns mysteriously blank.
 *
 * "Audit history is append-only in UI. Do not present edit or delete actions."
 * There is no such control here, and a test asserts there never is.
 */
const AUDIT_CATEGORIES = ["policy", "action", "risk"];

/* The result of an entry: policy records an outcome; an action's result is in
 * its own name, because `ACTION_SUCCEEDED` and `ACTION_FAILED` are different
 * events rather than one event with a field. */
const ACTION_RESULTS = {
  ACTION_REQUESTED: "result_pending",
  ACTION_SUCCEEDED: "result_succeeded",
  ACTION_FAILED: "result_failed",
  ACTION_CANCELLED: "result_cancelled",
  ACTION_EXPIRED: "result_expired",
  ACTION_EXPIRED_BEFORE_DISPATCH: "result_expired",
  ACTION_DEDUPLICATED: "result_skipped",
  ACTION_COMPENSATED: "result_reversed",
  ACTION_CANCELLED_BY_MANUAL_OVERRIDE: "result_overridden",
};

function auditResult(entry) {
  if (entry.outcome) return t(`policy_${entry.outcome}`);
  const key = ACTION_RESULTS[entry.action];
  return key ? t(key) : "—";
}

function auditTarget(entry) {
  if (!entry.device_id) {
    if (!entry.capability) return "—";
    /* A technician sees the identifier here for the same reason they see it
       everywhere else: it is what they will type into a diagnostic. */
    return may("READ_DIAGNOSTICS")
      ? el("span", "identifier", entry.capability)
      : friendlyCapability(entry.capability);
  }
  const wrap = el("span", "device-name");
  wrap.append(link(`#/devices/${entry.device_id}`, null, entry.device_id));
  if (entry.capability) {
    wrap.append(
      el("span", "type-caption muted",
        may("READ_DIAGNOSTICS") ? entry.capability : friendlyCapability(entry.capability)),
    );
  }
  return wrap;
}

function auditReason(entry) {
  if (entry.reason) return entry.reason;
  const codes = entry.reason_codes || [];
  return codes.length ? codes.join(", ") : "—";
}

/* ── users and roles (§21, UI-5) ──

   Two things this screen does that a permissions table usually does not.

   It shows revoked and expired members rather than hiding them: "who used to
   have a key" is the question asked after something goes missing, and a list
   that only shows the present cannot answer it.

   And it will not let a change through without a reason. That is not a form
   validation nicety — the reason is the audit entry somebody reads months
   later, and "role changed" answers nothing. */

async function renderUsers(host) {
  const home = state.homeId;
  const { data, failed } = await loadHomeView({
    users: api(`/v1/homes/${home}/users`),
  });
  if (!data.users) {
    host.append(failureNotice(errorFor(failed, "users"), t("source_users")));
    return;
  }

  const { members = [], may_manage: mayManage, assignable_roles: assignable = [] } = data.users;

  const management = data.users.management || {};
  if (management.managed_by) {
    /* Said before the member list, not after it. Somebody scrolling this
       screen is asking who can see their home, and the answer starts with the
       company that manages it. */
    host.append(
      notice(
        "partial",
        t("managed_by_title").replace("{company}", management.managed_by),
        t("managed_by_detail"),
      ),
    );
  }

  if (!mayManage) {
    /* §20: say why the controls are absent rather than rendering a page that
       looks broken. */
    host.append(notice("partial", t("users_readonly_title"), t("users_readonly_detail")));
  } else {
    host.append(inviteForm(home, assignable));
  }

  if (!members.length) {
    host.append(emptyNotice("no_members"));
    return;
  }

  if (mayManage) host.append(panelSection(home));

  const rows = members.map((member) => {
    const who = el("div");
    who.append(el("span", "identifier", member.display_name || member.subject));
    if (member.display_name && member.display_name !== member.subject) {
      who.append(el("p", "muted", member.subject));
    }
    return [
      who,
      t(`role_${member.role.toLowerCase()}`),
      member.active
        ? badge("online", t("access_active"))
        : badge("offline", member.revoked_at ? t("access_revoked") : t("access_expired")),
      member.expires_at ? when(member.expires_at) : t("access_no_expiry"),
      member.granted_by,
      mayManage && member.active ? revokeButton(home, member) : el("span", "muted", "—"),
    ];
  });

  host.append(
    scrollableTable(
      ["who", "role", "access_state", "expires", "granted_by", "manage"],
      rows,
    ),
  );
}

/* ── wall panels ──
 *
 * Registered here rather than on the panel itself, because a screen on a wall
 * that can enrol itself is a screen anybody in the hallway can enrol. The
 * owner decides where a permanent control surface goes.
 *
 * The token is shown once and never again. That is what makes revoking one
 * mean something: a panel that lost its token is re-registered, not recovered.
 */

function panelSection(home) {
  const section = el("section", "card");
  section.append(el("h2", "type-section-title", t("panels_title")));
  section.append(el("p", "muted", t("panels_detail")));

  const listing = el("div");
  section.append(listing);

  const location = labelledInput("panel-location", t("panel_location"), "text");
  const reason = labelledInput("panel-reason", t("reason_for_change"), "text");
  const add = el("button", "btn btn--primary", t("panel_add"));
  add.type = "button";
  const outcome = el("div");
  section.append(location.node, reason.node, add, outcome);

  async function load() {
    listing.replaceChildren();
    try {
      const body = await api(`/v1/homes/${home}/panels`);
      const panels = body.panels || [];
      if (!panels.length) {
        listing.append(el("p", "muted", t("no_panels")));
        return;
      }
      listing.append(
        scrollableTable(
          ["who", "access_state", "granted_by", "manage"],
          panels.map((panel) => [
            panel.display_name || panel.subject,
            panel.active ? badge("online", t("access_active")) : badge("offline", t("access_revoked")),
            panel.granted_by,
            panel.active ? revokeButton(home, panel) : el("span", "muted", "—"),
          ]),
        ),
      );
    } catch (error) {
      listing.append(failureNotice(error, t("source_users")));
    }
  }

  add.addEventListener("click", async () => {
    outcome.replaceChildren();
    if (!location.input.value.trim() || !reason.input.value.trim()) {
      outcome.append(notice("error", t("reason_required"), t("reason_required_detail")));
      return;
    }
    add.setAttribute("aria-busy", "true");
    try {
      const created = await api(`/v1/homes/${home}/panels`, {
        method: "POST",
        body: JSON.stringify({
          location: location.input.value.trim(),
          reason: reason.input.value.trim(),
        }),
      });
      /* Shown once, and said so. A household that closes this without copying
         it registers the panel again — which is the same rule every other
         credential here follows. */
      const shown = notice(
        "partial",
        t("panel_token_title"),
        t("panel_token_detail").replace("{url}", `${window.location.origin}/panel/`),
      );
      const code = el("p", "identifier", created.token);
      shown.append(code);
      outcome.append(shown);
      location.input.value = "";
      reason.input.value = "";
      await load();
    } catch (error) {
      outcome.append(failureNotice(error, t("source_users")));
    } finally {
      add.removeAttribute("aria-busy");
    }
  });

  load();
  return section;
}

function inviteForm(home, assignable) {
  const form = el("form", "card");
  form.append(el("h2", "type-section-title", t("invite_title")));
  form.append(el("p", "muted", t("invite_detail")));

  const subject = labelledInput("invite-subject", t("who"), "text");
  const role = el("select", "select");
  role.id = "invite-role";
  for (const value of assignable) {
    const option = el("option", null, t(`role_${value.toLowerCase()}`));
    option.value = value;
    role.append(option);
  }
  const roleField = el("div", "field");
  const roleLabel = el("label", null, t("role"));
  roleLabel.htmlFor = role.id;
  roleField.append(roleLabel, role);

  const reason = labelledInput("invite-reason", t("reason_for_change"), "text");
  /* `required` stays for the semantics a screen reader announces. Native
     validation is turned off because its bubble is the browser's language, not
     the household's, and §20 asks for a designed state rather than a tooltip
     that appears in English on an Arabic screen. */
  reason.input.required = true;
  form.noValidate = true;

  const submit = el("button", "btn btn--primary", t("invite_submit"));
  submit.type = "submit";

  const outcome = el("div");
  form.append(subject.node, roleField, reason.node, submit, outcome);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    outcome.replaceChildren();
    if (!reason.input.value.trim()) {
      /* Refused here as well as by the server: a person should learn what is
         missing without a round trip, and the server must not rely on it. */
      outcome.append(notice("error", t("reason_required"), t("reason_required_detail")));
      reason.input.focus();
      return;
    }
    submit.setAttribute("aria-busy", "true");
    try {
      await api(`/v1/homes/${home}/users`, {
        method: "POST",
        body: JSON.stringify({
          subject: subject.input.value.trim(),
          role: role.value,
          reason: reason.input.value.trim(),
        }),
      });
      await refresh();
    } catch (error) {
      outcome.append(failureNotice(error, t("source_users")));
    } finally {
      submit.removeAttribute("aria-busy");
    }
  });
  return form;
}

function revokeButton(home, member) {
  const button = el("button", "btn btn--secondary", t("revoke"));
  button.type = "button";
  button.addEventListener("click", async () => {
    /* A reason, before anything happens. Revoking access is exactly the change
       whose "why" gets asked about later. */
    const reason = window.prompt(t("reason_for_change"));
    if (!reason || !reason.trim()) return;
    button.setAttribute("aria-busy", "true");
    try {
      await api(`/v1/homes/${home}/users/${member.membership_id}/revoke`, {
        method: "POST",
        body: JSON.stringify({ reason: reason.trim() }),
      });
      await refresh();
    } finally {
      button.removeAttribute("aria-busy");
    }
  });
  return button;
}

function labelledInput(id, label, type) {
  const node = el("div", "field");
  const element = el("label", null, label);
  element.htmlFor = id;
  const input = el("input", "input");
  input.id = id;
  input.type = type;
  node.append(element, input);
  return { node, input };
}

async function renderAudit(host) {
  const { data, failed } = await loadHomeView({
    audit: api(`/v1/audit?home_id=${state.homeId}&limit=200`),
  });
  if (!data.audit) {
    host.append(failureNotice(errorFor(failed, "audit"), t("source_audit")));
    return;
  }
  const items = data.audit.items || [];
  if (!items.length) {
    host.append(emptyNotice("no_audit"));
    return;
  }

  host.append(notice("partial", t("audit_readonly_title"), t("audit_readonly_detail")));

  const filters = el("div", "filters");
  const categoryFilter = selectFilter(
    "audit-category", t("event_category"), t("all_categories"),
    AUDIT_CATEGORIES, (value) => t(`category_${value}`),
  );
  const actors = [...new Set(items.map((entry) => entry.actor).filter(Boolean))].sort();
  const actorFilter = selectFilter("audit-actor", t("who"), t("all_actors"), actors);
  filters.append(categoryFilter.node, actorFilter.node);
  const summary = el("span", "filter-summary");
  filters.append(summary);
  host.append(filters);

  const results = el("div");
  host.append(results);

  function apply() {
    const category = categoryFilter.select.value;
    const actor = actorFilter.select.value;
    const shown = items.filter(
      (entry) =>
        (category === "" || entry.source === category) &&
        (actor === "" || entry.actor === actor),
    );
    summary.textContent = t("audit_summary")
      .replace("{shown}", shown.length)
      .replace("{total}", items.length);
    results.replaceChildren();
    if (!shown.length) {
      results.append(notice("partial", t("no_matches"), t("no_audit_matches_detail")));
      return;
    }
    const headings = ["when", "event_category", "what", "target", "who", "why", "result"];
    results.append(
      scrollableTable(
        headings,
        shown.map((entry) => [
          when(entry.occurred_at),
          badge(entry.source === "risk" ? "error" : "unknown", t(`category_${entry.source}`)),
          entry.action,
          auditTarget(entry),
          entry.actor || t("actor_platform"),
          auditReason(entry),
          auditResult(entry),
        ]),
      ),
    );
  }

  categoryFilter.select.addEventListener("change", apply);
  actorFilter.select.addEventListener("change", apply);
  apply();

  /* §17.14 also lists role and correlation ID. Neither is written when the
     event happens, so neither can be shown later without inventing it. */
  host.append(notice("partial", t("audit_fields_missing"), t("audit_fields_missing_detail")));
}

/* ── §17.15 System Health ── */

async function renderHealth(host) {
  const { data, failed } = await loadHomeView({
    status: api("/v1/system/status"),
    actions: api(`/v1/homes/${state.homeId}/actions`),
  });
  if (!data.status) {
    host.append(failureNotice(errorFor(failed, "status"), t("source_status")));
    return;
  }
  const components = Object.entries(data.status.components || {});
  const unhealthy = components.filter(([, value]) => value !== "ok");

  /* There is no `healthy` flag in the response, and inventing one in the
     console would be a second definition of health. The component list is the
     platform's own answer; the summary only counts it. */
  host.append(
    notice(
      unhealthy.length ? "failure" : "partial",
      unhealthy.length
        ? t("health_degraded_title").replace("{n}", unhealthy.length)
        : t("health_ok_title"),
      unhealthy.length ? unhealthy.map(([name]) => name).join(", ") : t("health_ok_detail"),
      `${t("checked_at")} ${clock(data.status.checked_at)}`,
    ),
  );

  /* §20: never show a normal state when the truth is more important. A hub
     that cannot act is not a degraded hub — it is a deliberate posture, and a
     household running a pilot should see it before anything else. */
  if (data.status.dispatch_enabled === false) {
    host.append(notice("stale", t("observe_only_title"), t("observe_only_detail")));
  }

  host.append(
    definitions([
      [t("hub"), el("span", "identifier", data.status.hub_id)],
      [t("can_act"), t(data.status.dispatch_enabled === false ? "no" : "yes")],
      [t("uptime"), duration(data.status.uptime_seconds)],
      [t("properties_count"), data.status.homes],
      [t("cloud"), t("local_only")],
    ]),
  );

  host.append(el("h2", "type-section-title", t("components")));
  host.append(
    scrollableTable(
      ["component", "status"],
      components.map(([name, value]) => [
        name,
        badge(value === "ok" ? "online" : "error", t(value === "ok" ? "state_online" : "state_error")),
      ]),
    ),
  );

  host.append(el("h2", "type-section-title", t("recent_actions")));
  host.append(actionTable(((data.actions && data.actions.items) || []).slice(0, 20)));

  /* §13.7: the timeline is what makes an automated action reviewable — who
     decided, who approved, what was dispatched, and whether a person
     overrode it. It needs the audit permission, because it names actors. */
  if (may("READ_AUDIT")) {
    host.append(el("h2", "type-section-title", t("action_timeline")));
    try {
      const audit = await api(`/v1/audit?home_id=${state.homeId}`);
      host.append(timeline((audit.items || []).slice(0, 20)));
    } catch (error) {
      host.append(failureNotice(error, t("source_audit")));
    }
  }
}

function renderSettings(host) {
  const column = el("div", "readable-column stack");

  /* §8.4 requires Comfortable and Compact. The tokens have carried both since
     UI-0 and nothing ever offered the choice — a density mode no one can
     select is a density mode the product does not have. */
  const appearance = el("div", "card");
  appearance.append(el("h2", "card__title", t("appearance")));
  appearance.append(el("p", "muted", t("appearance_detail")));
  appearance.append(
    settingRow("density", t("density"), [
      ["comfortable", t("density_comfortable")],
      ["compact", t("density_compact")],
    ], currentDensity(), applyDensity),
  );
  column.append(appearance);

  const privacy = el("div", "card");
  privacy.append(el("h2", "card__title", t("tab_privacy")));
  privacy.append(el("p", "muted", t("privacy_note")));
  privacy.append(el("p", null, `${t("cloud_sync")}: ${t("disabled")}`));
  if (may("MANAGE_PRIVACY")) {
    const actions = el("div", "row");
    const exportButton = el("button", "btn btn--secondary", t("export_data"));
    exportButton.type = "button";
    const deleteButton = el("button", "btn btn--destructive", t("delete_data"));
    deleteButton.type = "button";
    /* Neither is wired: export and deletion run through the operator scripts
       (`make diagnostics`, the privacy tooling), and putting a household's
       whole record behind one unconfirmed click in a console would be the
       kind of one-click destructive action §21 rules out. */
    for (const button of [exportButton, deleteButton]) {
      button.disabled = true;
    }
    actions.append(exportButton, deleteButton);
    privacy.append(actions);
    privacy.append(el("p", "type-caption muted", t("privacy_via_operator")));
  } else {
    privacy.append(notice("denied", t("denied_title"), t("privacy_requires_permission")));
  }
  column.append(privacy);

  const session = el("div", "card");
  session.append(el("h2", "card__title", t("session")));
  session.append(
    definitions([
      [t("signed_in_as"), state.me.subject],
      [t("role"), state.me.role],
      [t("property"), el("span", "identifier", state.homeId)],
      [t("permissions"), state.me.permissions.map((p) => t(`permission_${p}`)).join(", ")],
    ]),
  );
  column.append(session);

  /* §17.13 users and roles, and §17.12 installations, would live here. Neither
     has a backend, and a permissions editor that cannot write is worse than
     none: it implies the change took effect. */
  column.append(notice("partial", t("platform_settings_missing"), t("platform_settings_missing_detail")));

  host.append(column);
}

function settingRow(id, label, options, current, onChange) {
  const field = el("div", "field");
  const labelNode = el("label", "field__label", label);
  labelNode.htmlFor = id;
  const select = el("select", "select");
  select.id = id;
  for (const [value, text] of options) {
    const option = el("option", null, text);
    option.value = value;
    select.append(option);
  }
  select.value = current;
  select.addEventListener("change", () => onChange(select.value));
  field.append(labelNode, select);
  return field;
}

function currentDensity() {
  return localStorage.getItem("syltra.density") || "comfortable";
}

function applyDensity(choice) {
  document.documentElement.dataset.density = choice;
  localStorage.setItem("syltra.density", choice);
}

function renderUnavailable(host, item) {
  /* §20: an absent capability is a designed state. It says which phase brings
     it, so the console is honest about being unfinished rather than broken. */
  const wrap = el("div", "readable-column");
  wrap.append(notice("partial", t(`nav_${item.id}`), t("not_yet_available")));
  host.append(wrap);
}

/* ── tables ── */

function scrollableTable(headings, rows) {
  /* §9.3 and §22: a device table is wider than 768px can hold, so it scrolls
     inside itself rather than pushing the page — and the scroll container is
     focusable, because a region only a mouse can reach cannot be read by
     keyboard. */
  const wrapper = el("div", "table-scroll table-scroll--pinned-header");
  wrapper.tabIndex = 0;
  wrapper.setAttribute("role", "region");
  wrapper.setAttribute("aria-label", t("table_label"));

  const table = el("table", "table");
  const thead = el("thead");
  const head = el("tr");
  for (const key of headings) {
    const cell = el("th", null, t(key));
    cell.scope = "col";
    head.append(cell);
  }
  thead.append(head);
  table.append(thead);

  const tbody = el("tbody");
  for (const cells of rows) {
    const row = el("tr");
    for (const cell of cells) {
      if (cell instanceof Node) {
        const td = el("td");
        td.append(cell);
        row.append(td);
      } else {
        row.append(el("td", null, cell));
      }
    }
    tbody.append(row);
  }
  table.append(tbody);
  wrapper.append(table);
  return wrapper;
}

/* ── banners (§9.3: critical risk stays at the top of the content) ── */

async function refreshBanners() {
  const banners = document.getElementById("banners");
  banners.replaceChildren();
  if (!may("READ_HOME") || !state.homeId) return;
  let cases = [];
  try {
    cases = (await api(`/v1/homes/${state.homeId}/risks`)).cases || [];
  } catch {
    return; /* The view itself reports the failure; a banner would repeat it. */
  }
  for (const item of cases.filter((c) => !c.advisory)) {
    const banner = el("div", "risk-banner");
    banner.setAttribute("role", "alert");
    banner.append(el("strong", null, `${t("confirmed")} — ${item.category}`));
    banner.append(document.createTextNode(` ${(item.reasons || [])[0] || ""}`));
    banners.append(banner);
  }
}

/* ── navigation rendering ── */

function buildNav() {
  const nav = document.getElementById("nav");
  nav.replaceChildren();
  for (const item of visibleNav()) {
    const link = el("a", "nav-item");
    link.href = `#/${item.id}`;
    link.id = `nav-${item.id}`;
    if (item.unavailable) link.dataset.unavailable = "true";
    link.append(el("span", "nav-item__icon", item.icon));
    link.querySelector(".nav-item__icon").setAttribute("aria-hidden", "true");
    link.append(el("span", "nav-item__label", t(`nav_${item.id}`)));
    nav.append(link);
  }
  markCurrent();
}

let navKeysBound = false;

/* The sidebar is a vertical list of links, so Up and Down move through it and
 * Home and End jump to the ends. Reading direction does not enter into it:
 * vertical order is the same in Arabic and English, which is exactly why the
 * horizontal tab strip this replaced needed direction-aware arrow keys and
 * this does not.
 *
 * Focus moves without navigating. Enter and Space activate, as they already do
 * for a link — a navigation item that changed the view on mere focus would
 * make the keyboard unusable for reaching the item below it. */
function bindNavKeys(nav) {
  nav.addEventListener("keydown", (event) => {
    const links = [...nav.querySelectorAll(".nav-item[href]")];
    const index = links.indexOf(document.activeElement);
    if (index < 0) return;
    let next = null;
    if (event.key === "ArrowDown") next = links[(index + 1) % links.length];
    else if (event.key === "ArrowUp") next = links[(index - 1 + links.length) % links.length];
    else if (event.key === "Home") next = links[0];
    else if (event.key === "End") next = links[links.length - 1];
    if (!next) return;
    event.preventDefault();
    next.focus();
  });
}

function markCurrent() {
  for (const link of document.querySelectorAll(".nav-item[href]")) {
    const selected = link.id === `nav-${state.view}`;
    if (selected) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
}

/* ── selections (§4: preserve the last valid workspace and property) ── */

function fillProperties() {
  const select = document.getElementById("property");
  select.replaceChildren();
  for (const home of state.me.homes) {
    const option = el("option", null, home);
    option.value = home;
    select.append(option);
  }
  select.value = state.homeId;
  select.disabled = state.me.homes.length < 2;

  /* One workspace exists today; the control is present because §4 requires it
     at the top, and it will list real workspaces when the backend has them. */
  const workspace = document.getElementById("workspace");
  workspace.replaceChildren();
  const only = el("option", null, t("workspace_default"));
  only.value = "default";
  workspace.append(only);
  workspace.disabled = true;
}

function chooseHome(requested) {
  /* A remembered property the token no longer covers is not an error — it is a
     stale preference. Fall back to the first home the caller can actually see
     rather than issuing requests that will 403. */
  const homes = state.me.homes;
  state.homeId = homes.includes(requested) ? requested : homes[0] || "";
  localStorage.setItem("syltra.home", state.homeId);
}

/* ── routing ── */

/* `#/devices` is a list; `#/devices/ac_living` is one device. Two segments at
 * most — §4 says breadcrumbs only when hierarchy exceeds two levels, and this
 * keeps the hierarchy at two so they are not needed. */
function currentRoute() {
  const [view, param] = location.hash.replace(/^#\/?/, "").split("/");
  const item = navItem(view);
  if (item && may(item.permission)) return { view, param: param ? decodeURIComponent(param) : null };
  const first = visibleNav()[0];
  return { view: first ? first.id : "overview", param: null };
}

async function route() {
  const { view, param } = currentRoute();
  state.view = view;
  state.param = param;
  // Leaving the screen releases whatever was being held on it.
  state.holdRefresh = false;
  markCurrent();
  const item = navItem(view);
  /* A detail view is titled by what it is showing, not by its section: a
     person on a device page wants to see the device's name at the top. */
  document.getElementById("page-title").textContent =
    param && item && item.detail ? param : t(`nav_${view}`);
  await refresh();
}

async function refresh() {
  const host = document.getElementById("view");
  const item = navItem(state.view);
  host.replaceChildren();
  if (!item) return;
  if (item.unavailable) {
    setStatus("");
    renderUnavailable(host, item);
    return;
  }

  /* §20 initial loading: a skeleton the size of what is coming, so the page
     does not jump when it arrives. */
  setStatus(t("loading"));
  host.append(loadingSkeleton());

  const render = state.param && item.detail ? item.detail : item.render;
  const staging = document.createDocumentFragment();
  try {
    await render(staging, state.param);
    host.replaceChildren(staging);
    setStatus("");
  } catch (error) {
    /* A renderer that threw outside a tolerated source is a bug or a total
       outage. Either way the person needs the specific reason, not "something
       went wrong" (§20). */
    host.replaceChildren(failureNotice(error, t(`nav_${state.view}`)));
    setStatus("");
  }
  await refreshBanners();
}

function loadingSkeleton() {
  const wrap = el("div", "stack");
  wrap.setAttribute("aria-hidden", "true");
  for (const size of ["3rem", "1.5rem", "1.5rem"]) {
    const bar = el("div", "skeleton");
    bar.style.blockSize = size;
    wrap.append(bar);
  }
  return wrap;
}

/* ── boot ── */

function bindSidebar() {
  const toggle = document.getElementById("sidebar-toggle");
  const collapsed = localStorage.getItem("syltra.sidebar") === "collapsed";
  setCollapsed(collapsed);
  toggle.addEventListener("click", () => {
    setCollapsed(document.documentElement.dataset.sidebar !== "collapsed");
  });
}

function setCollapsed(collapsed) {
  const toggle = document.getElementById("sidebar-toggle");
  if (collapsed) document.documentElement.dataset.sidebar = "collapsed";
  else delete document.documentElement.dataset.sidebar;
  toggle.setAttribute("aria-expanded", String(!collapsed));
  toggle.querySelector(".nav-item__label").textContent = t(
    collapsed ? "expand_sidebar" : "collapse_sidebar",
  );
  localStorage.setItem("syltra.sidebar", collapsed ? "collapsed" : "expanded");
}

function showSignedOut(message) {
  document.getElementById("view").replaceChildren(
    el("p", "state-notice state-notice--error", message),
  );
  document.getElementById("nav").replaceChildren();
}

async function boot() {
  await loadDictionary();
  applyLocale();

  const appearance = localStorage.getItem("syltra.appearance") || "system";
  applyAppearance(appearance);
  applyDensity(currentDensity());
  document.getElementById("appearance").value = appearance;
  document.getElementById("appearance").addEventListener("change", (event) => {
    applyAppearance(event.target.value);
  });

  document.getElementById("locale").value = state.locale;
  document.getElementById("locale").addEventListener("change", (event) => {
    state.locale = event.target.value;
    applyLocale();
    buildNav();
    route();
  });

  bindSidebar();

  document.getElementById("sign-out").addEventListener("click", () => {
    localStorage.removeItem("syltra.token");
    state.token = "";
    showSignedOut(t("signed_out"));
  });

  try {
    state.me = await api("/v1/me");
  } catch (error) {
    showSignedOut(error.message);
    return;
  }

  const requested =
    new URLSearchParams(location.search).get("home") ||
    localStorage.getItem("syltra.home") ||
    "";
  chooseHome(requested);
  fillProperties();
  document.getElementById("property").addEventListener("change", (event) => {
    chooseHome(event.target.value);
    route();
  });

  document.getElementById("account-name").textContent =
    state.me.display_name || state.me.subject;
  document.getElementById("account-role").textContent = state.me.role;

  buildNav();
  if (!navKeysBound) {
    bindNavKeys(document.getElementById("nav"));
    navKeysBound = true;
  }
  window.addEventListener("hashchange", route);
  await route();
  connectStream();
  /* The poll is now the fallback, not the mechanism. It stays because a
     WebSocket can fail in ways that look like success — a proxy that holds the
     connection open and delivers nothing — and a console that stopped updating
     without saying so is worse than one that updates slowly. */
  setInterval(() => {
    if (state.holdRefresh) return;
    if (state.stream.healthy) return;
    refresh();
  }, 15000);
}

/* ── the live change feed ──

   The stream carries notifications, not data: "something changed, and here is
   how far the sequence has advanced". The console then re-reads the endpoints
   it already reads, so there is exactly one description of a device and the
   socket is not a second one that can disagree with it. */

const STREAM_BACKOFF_MS = [500, 1000, 2000, 5000, 10000, 30000];

function streamUrl() {
  /* `/v1/stream`, spelled out. `API` is the empty string here and every other
     call writes its own `/v1/...`, so building this one from `API` alone
     produced `ws://host/stream` — a 404 that the retry loop then hid behind
     patient, well-behaved reconnection. */
  const url = new URL(`${API}/v1/stream`, window.location.href);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  /* A token in a URL is normally wrong. A browser cannot set headers on a
     WebSocket handshake, so there is no alternative here; the connection is to
     this machine, and the gateway verifies before accepting. */
  url.searchParams.set("token", state.token);
  url.searchParams.set("home_id", state.homeId);
  url.searchParams.set("cursor", String(state.stream.cursor));
  return url.toString();
}

function connectStream() {
  if (!state.homeId || !state.token) return;
  if (state.stream.socket) {
    state.stream.socket.onclose = null;
    state.stream.socket.close();
  }
  let socket;
  try {
    socket = new WebSocket(streamUrl());
  } catch {
    scheduleStreamRetry();
    return;
  }
  state.stream.socket = socket;

  socket.onopen = () => {
    state.stream.attempt = 0;
  };

  socket.onmessage = (event) => {
    let message;
    try {
      message = JSON.parse(event.data);
    } catch {
      return;
    }
    state.stream.healthy = true;
    state.stream.lastMessageAt = Date.now();
    if (typeof message.seq === "number") state.stream.cursor = message.seq;

    if (message.type === "connected") {
      /* `resync` and "you missed nothing" must not be treated alike: the first
         means the server cannot say what was missed, and only a re-read is
         safe. */
      if (message.resync || (message.missed || []).length) refreshUnlessHeld();
      return;
    }
    if (message.type === "changed") refreshUnlessHeld();
  };

  socket.onclose = () => {
    state.stream.healthy = false;
    scheduleStreamRetry();
  };
  socket.onerror = () => {
    state.stream.healthy = false;
  };
}

function refreshUnlessHeld() {
  /* Same rule the poll follows: a test run's result is an answer somebody
     asked for, and a change elsewhere in the house must not wipe it. */
  if (state.holdRefresh) return;
  /* Coalesce a burst arriving as separate frames into one re-read. */
  clearTimeout(state.stream.pending);
  state.stream.pending = setTimeout(() => refresh(), 120);
}

function scheduleStreamRetry() {
  const attempt = Math.min(state.stream.attempt, STREAM_BACKOFF_MS.length - 1);
  /* Jitter, so a hub that restarted does not get every console in the house
     reconnecting in the same millisecond. */
  const delay = STREAM_BACKOFF_MS[attempt] * (0.75 + Math.random() * 0.5);
  state.stream.attempt += 1;
  clearTimeout(state.stream.retry);
  state.stream.retry = setTimeout(connectStream, delay);
}

boot();
