/* The wall panel's own copy of itself.
 *
 * The platform has never needed the internet. What it did need was the hub: the
 * panel is *served by* the hub, so a hub that is restarting — an update, a power
 * cut, a router rebooting first — left a browser error page on somebody's wall
 * where a control surface used to be. That is the worst possible failure for a
 * device whose whole job is to be there.
 *
 * This keeps the shell — the page, the styles, the script, the wording, the
 * fonts — on the panel itself, so it starts with nothing reachable and says so
 * in its own typeface.
 *
 * ## The one rule
 *
 * **Nothing under `/v1/` is ever cached, and never served from cache.** A
 * cached light switch on a wall is worse than a blank one, because somebody
 * trusts it: they press "off", the tile goes dark, and the light is still on in
 * a room they have already left. Device state comes from the hub or it does not
 * come at all — the panel is allowed to keep its own face offline, never its
 * own idea of the house.
 *
 * ## Staying current without reloading under somebody's hand
 *
 * Shell files are answered from cache and revalidated behind the request, so a
 * panel that has been on the wall for two years is not two years out of date. A
 * changed ETag is reported to the page, which reloads at a quiet moment — never
 * while a hazard is on screen, never seconds after somebody pressed something.
 *
 * ## Where this does not run
 *
 * Service workers need a secure context. `http://hub.local/panel/` on a LAN is
 * not one, so on a plain-HTTP hub none of this registers and the panel behaves
 * exactly as it did before — which is why the gateway also sends cache headers
 * that let the browser's own cache cover the same case less well. A hub with a
 * local certificate is the real fix and it is a decision, not code.
 */

const VERSION = "v1";
const SHELL = `syltra-panel-${VERSION}`;

/* The whole panel, and nothing that is not the panel. */
const ASSETS = [
  "./",
  "./index.html",
  "./panel.css",
  "./panel.js",
  "./i18n.json",
  "/design-system/typography/fonts.css",
  "/design-system/tokens/tokens.css",
  "/design-system/themes/dark-theme.css",
  "/design-system/themes/light-theme.css",
  "/design-system/typography/typography.css",
  "/design-system/tokens/motion.css",
  "/design-system/foundation.css",
  "/design-system/primitives.css",
  /* Arabic and Latin, at the weights the panel actually uses. A panel that
     falls back to a system font when the hub is down looks broken in a way
     nobody can explain. */
  "/design-system/typography/fonts/IBMPlexSansArabic-Regular.woff2",
  "/design-system/typography/fonts/IBMPlexSansArabic-Medium.woff2",
  "/design-system/typography/fonts/IBMPlexSansArabic-SemiBold.woff2",
  "/design-system/typography/fonts/Inter-Regular.woff2",
  "/design-system/typography/fonts/Inter-Medium.woff2",
  "/design-system/typography/fonts/Inter-SemiBold.woff2",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(SHELL)
      /* Individually, not addAll: addAll fails the whole install if one file
         404s, which would leave a panel with no offline copy at all because a
         font was renamed. */
      .then((cache) => Promise.allSettled(ASSETS.map((asset) => cache.add(asset))))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((names) => Promise.all(names.filter((n) => n !== SHELL).map((n) => caches.delete(n))))
      .then(() => self.clients.claim()),
  );
});

async function tell(message) {
  const clients = await self.clients.matchAll({ type: "window" });
  for (const client of clients) client.postMessage(message);
}

async function fromCacheFirst(request) {
  const cache = await caches.open(SHELL);
  const cached = await cache.match(request, { ignoreSearch: true });

  /* `no-cache` so this asks the hub rather than the browser's own cache. The
     gateway sends a five-minute max-age for the sake of panels that cannot run
     a service worker; where one *is* running, it should be the thing that
     decides what is current, and a revalidation answered from the same cache it
     is trying to refresh would never notice an update at all. */
  const revalidate = fetch(request, { cache: "no-cache" })
    .then(async (response) => {
      if (!response.ok) return response;
      const changed = cached && cached.headers.get("ETag") !== response.headers.get("ETag");
      await cache.put(request, response.clone());
      /* The page decides when to act on this. A service worker reloading a wall
         panel the moment a file changes is a panel that goes blank while
         somebody is reaching for it. */
      if (changed) await tell({ type: "SHELL_UPDATED" });
      return response;
    })
    .catch(() => null);

  if (cached) return cached;
  const fresh = await revalidate;
  if (fresh) return fresh;
  /* Offline, and never seen this file. For a navigation that still means the
     panel rather than the browser's error page. */
  if (request.mode === "navigate") {
    const shell = await cache.match("./index.html");
    if (shell) return shell;
  }
  return new Response("", { status: 504, statusText: "offline" });
}

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  /* The one rule. Device state is the hub's to answer, and a stale answer is
     worse than none — so this path is left entirely to the network, which also
     means an offline press fails loudly instead of appearing to work. */
  if (url.pathname.startsWith("/v1/")) return;

  event.respondWith(fromCacheFirst(request));
});
