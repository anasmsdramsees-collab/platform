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

function controlFor(device, capability, reading) {
  const button = el("button", "control");
  button.type = "button";
  button.dataset.deviceId = device.device_id;
  button.dataset.capability = capability;

  const isBoolean = typeof reading.value === "boolean";
  const on = reading.value === true;
  if (isBoolean) button.dataset.on = String(on);

  button.append(
    el("span", "control__name", device.name || device.device_id),
    el(
      "span",
      "control__state",
      isBoolean ? (on ? t("on") : t("off")) : `${reading.value}${reading.unit || ""}`,
    ),
  );

  /* Booleans only. A wall panel is a light switch, and a temperature dial with
     no room to drag needs a screen somebody is looking at. */
  if (!isBoolean) {
    button.disabled = true;
    return button;
  }

  button.addEventListener("click", () => operate(button, device.device_id, capability, !on));
  return button;
}

async function operate(button, deviceId, capability, value) {
  const key = `${deviceId}:${capability}`;
  if (state.busy.has(key)) return;
  state.busy.add(key);
  button.setAttribute("aria-busy", "true");
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
    button.removeAttribute("aria-busy");
  }
}

function setStatus(text, isError = false) {
  const status = document.getElementById("status");
  status.textContent = text;
  status.dataset.error = String(Boolean(isError));
}

/* ── one pass ── */

async function refresh() {
  let devices;
  let risks;
  try {
    [devices, risks] = await Promise.all([
      api(`/v1/homes/${state.homeId}/devices`),
      api(`/v1/homes/${state.homeId}/risks`),
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
      if (!reading.operable) continue;
      if (typeof reading.value !== "boolean") continue;
      if (reading.status !== "KNOWN") continue;
      controls.append(controlFor(device, capability, reading));
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
  const response = await fetch("./i18n.json");
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
