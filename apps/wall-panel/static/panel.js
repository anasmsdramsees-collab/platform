/* SYLTRA wall panel.
 *
 * The panel shows what it may operate and nothing else. It does not render a
 * greyed-out lock: a disabled control still tells whoever is standing in the
 * hallway that a lock exists and that this screen is the way to it, which is
 * exactly what a panel by the front door should not advertise.
 *
 * What it may operate is decided by the server, from the token the panel holds.
 * There is no list of allowed capabilities in this file — a second copy of that
 * rule is a second copy that can drift from the first, and the one that matters
 * is the one the API enforces.
 */

const API = "";

const state = {
  token: localStorage.getItem("syltra.panel.token") || "",
  homeId: localStorage.getItem("syltra.panel.home") || "",
  locale: localStorage.getItem("syltra.panel.locale") || "en",
  dict: {},
  busy: new Set(),
};

/* Where the panel hangs. Shown in the header, and it is also what the audit
   trail will say — "the hall panel", not "somebody". */
const PLACE = localStorage.getItem("syltra.panel.place") || "";

const REFRESH_MS = 5000;
const NIGHT_FROM = 22;
const NIGHT_UNTIL = 6;

async function api(path, options = {}) {
  const separator = path.includes("?") ? "&" : "?";
  const response = await fetch(`${API}${path}${separator}locale=${state.locale}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "Accept-Language": state.locale,
      ...(state.token ? { Authorization: `Bearer ${state.token}` } : {}),
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    const error = new Error(`${response.status}`);
    error.status = response.status;
    throw error;
  }
  return response.json();
}

function t(key) {
  const table = state.dict[state.locale] || state.dict.en || {};
  return table[key] || key;
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = text;
  return node;
}

/* ── the hazard, which takes the screen ── */

function showHazard(risks) {
  const hazard = document.getElementById("hazard");
  const confirmed = (risks.cases || []).find((c) => !c.advisory);
  if (!confirmed) {
    hazard.hidden = true;
    return false;
  }

  document.getElementById("hazard-what").textContent = t(
    `hazard_${confirmed.category.toLowerCase()}`,
  );
  document.getElementById("hazard-where").textContent = confirmed.room_id
    ? t("hazard_where").replace("{room}", confirmed.room_id)
    : "";

  /* What the platform has already done, in the same breath as the alarm. A
     household reading "gas detected" needs to know whether the valve is shut
     without walking to the kitchen to look. */
  const plan = confirmed.response_plan;
  const carriedOut = plan && (plan.isolating || []).some((step) => step.carried_out);
  document.getElementById("hazard-done").textContent = carriedOut
    ? t("hazard_isolated")
    : t("hazard_not_isolated");

  hazard.hidden = false;
  return true;
}

/* ── the controls ── */

/* A glyph per capability domain, so a tile is recognisable before somebody is
   close enough to read its label. Text, not artwork: an icon set is a thing to
   draw, license and maintain, and a wall panel needs six shapes rather than a
   family. Marked aria-hidden because the label beside it already says what it
   is — a screen reader announcing "light bulb, Living room light" says it
   twice. */
const GLYPHS = {
  light: "☀",
  switch: "⏻",
  climate: "❄",
  cover: "▤",
  fan: "✳",
};

function glyphFor(capability) {
  return GLYPHS[capability.split(".", 1)[0]] || "◉";
}

/* A unit as it is written next to a number on a wall rather than in a data
   sheet. Presentation only — nothing here decides what may be operated. */
const UNIT_SUFFIX = { C: "°", "%": "%" };

function suffixFor(unit) {
  return UNIT_SUFFIX[unit] || (unit ? ` ${unit}` : "");
}

function nameOf(device) {
  return el("span", "control__name", device.name || device.device_id);
}

/* A switch: the whole tile is the target, because a button inside a card asks
   somebody to aim and a tile asks them to hit a wall. */
function toggleTile(device, capability, reading) {
  const button = el("button", "control");
  button.type = "button";
  button.dataset.deviceId = device.device_id;
  button.dataset.capability = capability;
  const on = reading.value === true;
  button.dataset.on = String(on);

  const icon = el("span", "control__icon", glyphFor(capability));
  icon.setAttribute("aria-hidden", "true");

  const body = el("span");
  body.append(nameOf(device), el("span", "control__state", on ? t("on") : t("off")));
  button.append(icon, body);
  button.addEventListener("click", () => operate(button, device.device_id, capability, !on));
  return button;
}

/* A dial: an air conditioner's temperature, a curtain's opening. The range and
   the size of one press come from the server, so this file holds no opinion
   about what any particular device can do — and a house in a climate where the
   air conditioning matters does not get a wall panel that omits it. */
function stepTile(device, capability, reading) {
  const control = reading.control;
  const node = el("div", "control control--step");
  node.dataset.deviceId = device.device_id;
  node.dataset.capability = capability;

  const stepper = el("div", "control__stepper");
  const buttons = [
    [-control.step, "−", "lower"],
    [control.step, "+", "raise"],
  ].map(([delta, label, key]) => {
    const button = el("button", "control__step", label);
    button.type = "button";
    /* The face of the button is a symbol, so it says what it does out loud. */
    button.setAttribute("aria-label", `${t(key)}: ${device.name || device.device_id}`);
    const target = Math.min(
      control.maximum,
      Math.max(control.minimum, Math.round((reading.value + delta) * 10) / 10),
    );
    /* At the end of the range the button stops rather than sending a value the
       server would refuse: a press that produces an error is worse than one
       that produces nothing. */
    button.disabled = target === reading.value;
    button.addEventListener("click", () => operate(node, device.device_id, capability, target));
    return button;
  });

  const value = el(
    "span",
    "control__reading",
    `\u2066${Math.round(reading.value).toLocaleString(state.locale)}${suffixFor(control.unit)}\u2069`,
  );
  stepper.append(buttons[0], value, buttons[1]);
  node.append(stepper, nameOf(device));
  return node;
}

function controlFor(device, capability, reading) {
  /* The server said how this is offered. The panel renders that — it does not
     decide that a temperature is a dial, it is told. */
  if (reading.control.kind === "TOGGLE") return toggleTile(device, capability, reading);
  if (reading.control.kind === "STEP") return stepTile(device, capability, reading);
  return null;
}

async function operate(node, deviceId, capability, value) {
  const key = `${deviceId}:${capability}`;
  if (state.busy.has(key)) return;
  state.busy.add(key);
  node.setAttribute("aria-busy", "true");
  setStatus("");
  try {
    await api(`/v1/homes/${state.homeId}/devices/${deviceId}/${capability}`, {
      method: "POST",
      body: JSON.stringify({ value }),
    });
    await refresh();
  } catch (error) {
    /* The server refused, and the panel says so plainly rather than snapping
       back to the old state as though nothing was pressed. */
    setStatus(error.status === 403 ? t("not_allowed_here") : t("did_not_work"), true);
  } finally {
    state.busy.delete(key);
    node.removeAttribute("aria-busy");
  }
}

function setStatus(text, isError = false) {
  const status = document.getElementById("status");
  status.textContent = text;
  status.dataset.error = String(Boolean(isError));
}

/* ── outside ──

   A weather app, except that none of it comes from a weather service. Every
   figure here was measured by a sensor on this building, which is why the band
   is still correct with the line to the internet cut — and why there is no
   "tomorrow" anywhere on it. What each reading is allowed to be called, and
   when it has gone stale, is decided by the server; this draws what it is sent.
*/

/* A figure, wrapped in a directional isolate.
   Arabic runs right to left and a bare "38°" inside an Arabic sentence gets
   rendered "°38" — the degree sign is direction-neutral, so it takes the
   direction of the text around it. The isolate says "this fragment has its own
   direction", which is true of every number on this panel. */
function number(value) {
  return `\u2066${value.toLocaleString(state.locale)}\u2069`;
}

function degrees(value) {
  return `\u2066${Math.round(value).toLocaleString(state.locale)}°\u2069`;
}

function ageLabel(seconds) {
  const minutes = Math.max(1, Math.round(seconds / 60));
  if (minutes < 60) return t("weather_minutes_ago").replace("{n}", number(minutes));
  return t("weather_hours_ago").replace("{n}", number(Math.round(minutes / 60)));
}

function detailCell(label, value, reading) {
  const cell = el("div", "weather__cell");
  cell.append(el("dt", "weather__label", label), el("dd", "weather__value", value));
  /* A stale reading is shown with its age rather than dropped: a blank where a
     humidity used to be reads as a broken panel, and "20 minutes ago" is
     useful. What it must never do is look current. */
  if (reading.stale) cell.append(el("dd", "weather__age", ageLabel(reading.age_seconds)));
  return cell;
}

/* A room as it is written on a wall. Common names have wording; anything a
   household called something of its own passes through untouched, because a
   room name is the household's own words and not a string to translate. */
function roomLabel(roomId) {
  if (!roomId) return "";
  const key = `room_${roomId}`;
  const table = state.dict[state.locale] || state.dict.en || {};
  return table[key] || roomId.replace(/_/g, " ");
}

function showWeather(weather) {
  const band = document.getElementById("weather");
  if (!weather || !weather.measured) {
    /* No sensor, so no weather. The panel does not fall back to an indoor
       thermometer relabelled as the sky, or the reverse. */
    band.hidden = true;
    return;
  }

  const readings = weather.readings || {};
  const temperature = readings["environment.temperature"];
  const humidity = readings["environment.humidity"];
  const air = readings["environment.air_quality"];
  const light = readings["environment.illuminance"];

  document.getElementById("weather-heading").textContent = t("weather_heading");

  /* ── outside ── */
  const outdoor = document.getElementById("weather-outdoor");
  outdoor.hidden = !temperature && !weather.condition;
  document.getElementById("weather-outdoor-where").textContent = t("weather_outside");
  document.getElementById("weather-temperature").textContent = temperature
    ? degrees(temperature.value)
    : "—";
  document.getElementById("weather-condition").textContent = weather.condition
    ? t(`weather_${weather.condition.toLowerCase()}`)
    : "";

  /* "Feels like" is withdrawn by the server when either input is stale, so a
     missing one here means the house cannot currently say. */
  const feels = document.getElementById("weather-feels");
  if (weather.feels_like_c !== null && weather.feels_like_c !== undefined) {
    feels.textContent = t("weather_feels").replace("{t}", degrees(weather.feels_like_c));
  } else if (temperature && temperature.stale) {
    feels.textContent = ageLabel(temperature.age_seconds);
  } else {
    feels.textContent = "";
  }

  /* ── inside ── */
  const indoorBand = document.getElementById("weather-indoor");
  const indoor = weather.indoor;
  indoorBand.hidden = !indoor;
  if (indoor) {
    /* The room is on the label, not implied. One thermometer in a five-room
       house is one room's temperature, and a panel that calls it "inside"
       without saying where is a panel making a claim it cannot support. */
    document.getElementById("weather-indoor-where").textContent = `${t("weather_inside")} · ${roomLabel(indoor.room_id)}`;
    document.getElementById("weather-indoor-temperature").textContent = degrees(indoor.value);

    const difference = document.getElementById("weather-difference");
    if (indoor.stale) {
      difference.textContent = ageLabel(indoor.age_seconds);
    } else if (weather.difference_c !== null && weather.difference_c !== undefined) {
      /* The number a household acts on: whether to open a window, whether the
         air conditioning is winning. */
      const gap = Math.abs(weather.difference_c);
      const key = weather.difference_c >= 0 ? "weather_cooler_by" : "weather_warmer_by";
      difference.textContent =
        Math.round(gap) === 0 ? t("weather_the_same") : t(key).replace("{n}", degrees(gap));
    } else {
      difference.textContent = "";
    }
  }

  document.getElementById("weather-source").textContent = t("weather_measured_here");

  const detail = document.getElementById("weather-detail");
  detail.replaceChildren();
  if (humidity) {
    detail.append(
      detailCell(
        t("weather_humidity"),
        `\u2066${Math.round(humidity.value).toLocaleString(state.locale)}%\u2069`,
        humidity,
      ),
    );
  }
  if (air && weather.air_band) {
    detail.append(detailCell(t("weather_air"), t(`air_${weather.air_band.toLowerCase()}`), air));
  }
  if (light) {
    detail.append(
      detailCell(
        t("weather_light"),
        t("weather_lux").replace("{n}", number(Math.round(light.value))),
        light,
      ),
    );
  }

  band.hidden = false;
}

/* ── one pass ── */

async function refresh() {
  let devices;
  let risks;
  let weather;
  try {
    [devices, risks, weather] = await Promise.all([
      api(`/v1/homes/${state.homeId}/devices`),
      api(`/v1/homes/${state.homeId}/risks`),
      /* The weather is the one thing here nobody depends on. A hub that cannot
         answer for outside should still show the lights, so this failure is
         swallowed while the other two are not. */
      api(`/v1/homes/${state.homeId}/weather`).catch(() => null),
    ]);
  } catch (error) {
    /* A panel that cannot reach the hub says so. It does not keep showing the
       last state it saw as though it were current — a stale light switch on a
       wall is worse than a blank one, because somebody trusts it. */
    setStatus(error.status === 401 ? t("not_registered") : t("no_hub"), true);
    return;
  }

  const items = devices.items || [];
  document.getElementById("place").textContent = PLACE || t("this_home");

  const attention = items.filter((d) => d.status && d.status !== "ONLINE").length;
  const allWell = document.getElementById("all-well");
  allWell.textContent = attention
    ? t("needs_attention").replace("{n}", String(attention))
    : t("all_well");
  allWell.dataset.attention = String(Boolean(attention));

  if (showHazard(risks)) return;

  showWeather(weather);

  const controls = document.getElementById("controls");
  const heading = document.getElementById("controls-heading");
  heading.textContent = t("controls_heading");
  controls.replaceChildren(heading);

  /* Only what the server sent. Capabilities this panel may not see are already
     absent from the payload, and capabilities it may not operate are refused
     when pressed — so the panel does not decide, it reflects. */
  for (const device of items) {
    for (const [capability, reading] of Object.entries(device.capabilities || {})) {
      /* The server says what this panel may press. Without it the panel was
         rendering a motion sensor and a gas alarm as buttons — pressable
         things that do nothing, next to a real light switch. */
      if (!reading.operable || !reading.control) continue;
      if (reading.status !== "KNOWN") continue;
      const node = controlFor(device, capability, reading);
      if (node) controls.append(node);
    }
  }
  if (controls.childElementCount === 1) {
    controls.append(el("p", "panel__status", t("nothing_to_control")));
  }
}

/* ── the clock, and the night ── */

function tick() {
  const now = new Date();
  document.getElementById("clock").textContent = now.toLocaleTimeString(state.locale, {
    hour: "2-digit",
    minute: "2-digit",
  });
  const hour = now.getHours();
  const night = hour >= NIGHT_FROM || hour < NIGHT_UNTIL;
  document.body.dataset.night = String(night);
}

async function boot() {
  /* Revalidated rather than taken from the cache. A wall panel is powered on
     for years without anybody reloading it, and a hub update that adds wording
     would otherwise leave the screen showing the previous dictionary — or,
     after a new key, the key itself. */
  const response = await fetch("./i18n.json", { cache: "no-cache" });
  state.dict = await response.json();
  document.documentElement.lang = state.locale;
  document.documentElement.dir = t("dir") === "rtl" ? "rtl" : "ltr";
  document.title = t("title");

  tick();
  setInterval(tick, 1000);

  if (!state.token || !state.homeId) {
    setStatus(t("not_registered"), true);
    return;
  }

  await refresh();
  /* Polling, not the stream: a panel that reconnects a socket every time the
     hub restarts is a panel showing an error at eye level in a hallway. Five
     seconds is fast enough for a light somebody just pressed, and the hazard
     path does not wait for it — a confirmed hazard is what the next pass will
     show, and the next pass is never more than five seconds away. */
  setInterval(refresh, REFRESH_MS);
}

boot();
