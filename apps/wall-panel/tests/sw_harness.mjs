/* A service worker with no browser to run it in.
 *
 * `sw.js` holds the one rule that makes an offline wall panel safe rather than
 * dangerous — device state is never cached — and there is no browser in the
 * test suite to prove it. So this builds the smallest environment a service
 * worker needs (a `self`, a `caches`, a `fetch`, a `Response`) and dispatches
 * the events at it, the way the browser would.
 *
 * Run: node sw_harness.mjs ../static/sw.js   → exits non-zero on the first
 * failure, with the assertion that failed. Driven by test_service_worker.py,
 * which skips when node is absent (the platform's toolchain is Python).
 */

import { readFileSync } from "node:fs";
import { createContext, runInContext } from "node:vm";
import { fileURLToPath } from "node:url";
import path from "node:path";

const ORIGIN = "http://hub.local";
/* Relative URLs inside a service worker resolve against the script's own
   address, not the site root — `./index.html` in /panel/sw.js means
   /panel/index.html. Getting this wrong in the harness would let a broken
   precache list pass. */
const BASE = `${ORIGIN}/panel/`;
const failures = [];

function check(name, condition) {
  if (!condition) failures.push(name);
}

/* ── the smallest browser that can hold a service worker ── */

class FakeHeaders {
  constructor(entries = {}) {
    this.entries = new Map(Object.entries(entries));
  }
  get(name) {
    return this.entries.get(name) ?? null;
  }
}

class FakeResponse {
  constructor(body = "", { status = 200, headers = {} } = {}) {
    this.body = body;
    this.status = status;
    this.ok = status >= 200 && status < 300;
    this.headers = new FakeHeaders(headers);
  }
  clone() {
    return new FakeResponse(this.body, {
      status: this.status,
      headers: Object.fromEntries(this.headers.entries),
    });
  }
}

function makeCaches() {
  const stores = new Map();
  const keyOf = (request) => {
    const url = new URL(typeof request === "string" ? request : request.url, BASE);
    return url.origin + url.pathname;
  };
  return {
    stores,
    async open(name) {
      if (!stores.has(name)) stores.set(name, new Map());
      const store = stores.get(name);
      return {
        async add(asset) {
          const response = await globalThis.__fetch(new FakeRequest(asset));
          if (!response.ok) throw new Error(`${asset}: ${response.status}`);
          store.set(keyOf(asset), response);
        },
        async put(request, response) {
          store.set(keyOf(request), response);
        },
        async match(request) {
          return store.get(keyOf(request)) ?? undefined;
        },
        async keys() {
          return [...store.keys()];
        },
      };
    },
    async keys() {
      return [...stores.keys()];
    },
    async delete(name) {
      return stores.delete(name);
    },
  };
}

class FakeRequest {
  constructor(url, { method = "GET", mode = "same-origin" } = {}) {
    this.url = new URL(url, BASE).toString();
    this.method = method;
    this.mode = mode;
  }
}

const harnessPath = fileURLToPath(import.meta.url);
const swPath = path.resolve(path.dirname(harnessPath), process.argv[2]);
const source = readFileSync(swPath, "utf8");

const listeners = new Map();
const messages = [];
let networkIsUp = true;
let served = new Map(); // pathname -> FakeResponse

globalThis.__fetch = async (request) => {
  if (!networkIsUp) throw new Error("offline");
  const url = new URL(typeof request === "string" ? request : request.url, BASE);
  const response = served.get(url.pathname);
  if (!response) return new FakeResponse("", { status: 404 });
  return response.clone();
};

const self = {
  location: { origin: ORIGIN },
  addEventListener: (type, handler) => listeners.set(type, handler),
  skipWaiting: async () => undefined,
  clients: {
    claim: async () => undefined,
    matchAll: async () => [{ postMessage: (m) => messages.push(m) }],
  },
};

const context = createContext({
  self,
  caches: makeCaches(),
  fetch: (request) => globalThis.__fetch(request),
  Response: FakeResponse,
  URL,
  console,
  Promise,
});
runInContext(source, context);

async function dispatch(type, event) {
  const handler = listeners.get(type);
  if (!handler) throw new Error(`no ${type} listener`);
  const waits = [];
  const target = {
    ...event,
    waitUntil: (p) => waits.push(p),
    respondWith: (p) => {
      target.responded = p;
    },
  };
  handler(target);
  await Promise.all(waits);
  return target;
}

/* ── what a wall panel needs to be true ── */

const SHELL = "./index.html";
served.set("/panel/index.html", new FakeResponse("<panel>", { headers: { ETag: "a" } }));
served.set("/panel/panel.js", new FakeResponse("script", { headers: { ETag: "a" } }));
served.set("/panel/panel.css", new FakeResponse("styles", { headers: { ETag: "a" } }));
served.set("/panel/i18n.json", new FakeResponse("{}", { headers: { ETag: "a" } }));
served.set("/panel/", new FakeResponse("<panel>", { headers: { ETag: "a" } }));
// Deliberately absent: every design-system asset. One missing file must not
// leave the panel with no offline copy at all.

self.location.href = `${ORIGIN}/panel/sw.js`;

await dispatch("install", {});
const cacheNames = await context.caches.keys();
check("install created exactly one cache", cacheNames.length === 1);
const store = context.caches.stores.get(cacheNames[0]);
check("the shell is cached despite missing design-system files", store.has(`${ORIGIN}/panel/panel.js`));
check("the page itself is cached", store.has(`${ORIGIN}/panel/index.html`));

/* The one rule. */
const api = await dispatch("fetch", {
  request: new FakeRequest(`${ORIGIN}/v1/homes/home_1/devices`),
});
check("device state is left entirely to the network", api.responded === undefined);
check("no API response was cached", ![...store.keys()].some((k) => k.includes("/v1/")));

/* A write is never intercepted either. */
const write = await dispatch("fetch", {
  request: new FakeRequest(`${ORIGIN}/panel/panel.js`, { method: "POST" }),
});
check("only GETs are answered from the panel's own copy", write.responded === undefined);

/* Offline: the shell comes from the panel itself. */
networkIsUp = false;
const offline = await dispatch("fetch", { request: new FakeRequest(`${ORIGIN}/panel/panel.js`) });
const offlineBody = await offline.responded;
check("a cached file is served with the hub down", offlineBody.body === "script");

const navigation = await dispatch("fetch", {
  request: new FakeRequest(`${ORIGIN}/panel/somewhere-new`, { mode: "navigate" }),
});
const navigationBody = await navigation.responded;
check("an unseen page falls back to the panel rather than a browser error", navigationBody.body === "<panel>");

/* Back up, with a changed file: the page is told, not reloaded. */
networkIsUp = true;
served.set("/panel/panel.js", new FakeResponse("newer", { headers: { ETag: "b" } }));
const revalidated = await dispatch("fetch", { request: new FakeRequest(`${ORIGIN}/panel/panel.js`) });
const revalidatedBody = await revalidated.responded;
check("the cached copy answers immediately", revalidatedBody.body === "script");
await new Promise((resolve) => setTimeout(resolve, 10));
check("a changed file is reported to the page", messages.some((m) => m.type === "SHELL_UPDATED"));
const updated = await (await context.caches.open(cacheNames[0])).match(`${ORIGIN}/panel/panel.js`);
check("and the next load gets the new one", updated.body === "newer");

if (failures.length) {
  console.error("FAILED:\n  " + failures.join("\n  "));
  process.exit(1);
}
console.log(`ok — ${SHELL} and ${store.size} files, no device state among them`);
