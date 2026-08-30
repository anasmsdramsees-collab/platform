// Generates the HEALTH subdomain's own root files into out/, overwriting the
// parent-site versions. Run after the static export, only for the health Pages
// project (see scripts/build-health.sh). Health lives on its own subdomain.
import { readdirSync, statSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const HOST = "https://health.syltraone.com";
const OUT = "out";
const EN_HEALTH = join(OUT, "en", "health");

if (!existsSync(EN_HEALTH)) {
  console.error("gen-health-root: out/en/health not found; run the build first.");
  process.exit(1);
}

// Collect every health route from the exported en/ tree (dirs with index.html),
// excluding the admin console.
function walk(dir, base) {
  let paths = [];
  if (existsSync(join(dir, "index.html"))) paths.push(base);
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) paths = paths.concat(walk(full, `${base}/${entry}`));
  }
  return paths;
}

const routes = walk(EN_HEALTH, "/health")
  .filter((p) => !p.includes("/admin"))
  .sort();

// ---- sitemap.xml (both locales + hreflang) ----
const today = new Date().toISOString().slice(0, 10);
const urls = routes
  .map((path) => {
    const en = `${HOST}/en${path}`;
    const ar = `${HOST}/ar${path}`;
    const priority = path === "/health" ? "1.0" : path.startsWith("/health/blog/") ? "0.7" : "0.8";
    const alt = `    <xhtml:link rel="alternate" hreflang="en" href="${en}"/>\n    <xhtml:link rel="alternate" hreflang="ar-SA" href="${ar}"/>\n    <xhtml:link rel="alternate" hreflang="x-default" href="${en}"/>`;
    return [
      `  <url>\n    <loc>${en}</loc>\n    <lastmod>${today}</lastmod>\n    <priority>${priority}</priority>\n${alt}\n  </url>`,
      `  <url>\n    <loc>${ar}</loc>\n    <lastmod>${today}</lastmod>\n    <priority>${priority}</priority>\n${alt}\n  </url>`,
    ].join("\n");
  })
  .join("\n");

const sitemap = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n${urls}\n</urlset>\n`;
writeFileSync(join(OUT, "sitemap.xml"), sitemap);

// ---- robots.txt (allow all, incl. AI answer engines; point to health sitemap) ----
const robots = `# SYLTRA HEALTH — health.syltraone.com
User-agent: *
Allow: /

# AI answer engines are welcome to read and cite these pages.
User-agent: OAI-SearchBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: Claude-User
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Google-Extended
Allow: /

Sitemap: ${HOST}/sitemap.xml
`;
writeFileSync(join(OUT, "robots.txt"), robots);

// ---- llms.txt (GEO: concise facts + Q&A for answer engines) ----
const llms = `# SYLTRA HEALTH

> SYLTRA HEALTH (Arabic: سيلترا هيلث) is a connected health intelligence layer within SYLTRA ONE, a Saudi technology group in Riyadh. It connects a person's body data with their home's movement and environment and their trusted circle, learns the person's normal pattern, adapts the home, and, when an unusual change appears, verifies with the person and helps reach the most suitable trusted person under a plan the person approves in advance. Slogan: "Your home knows when something changes." Aligned with Saudi Vision 2030.

Site: ${HOST}. Contact: info@syltraone.com.

## What it is
- Not a data dashboard and not a separate emergency system. It is a health intelligence layer that makes the home understand the person within the context of daily life.
- Core layers: Connected Health (approved health and fitness data), Home Awareness (movement, presence, environment), Personal Baseline (each person's normal pattern), Adaptive Environment (home settings the user approved), Intelligent Response (verification, alerting a trusted person, approved escalation).

## Key pages
- ${HOST}/en/health : home (the concept: watch, understand, respond).
- ${HOST}/en/health/how-it-works : signals to response, the five components, response flow, setup.
- ${HOST}/en/health/app : the app (Today, Pattern, Home, Circle, Settings).
- ${HOST}/en/health/older-adults , /chronic-conditions , /chronic-conditions/blood-pressure , /chronic-conditions/diabetes , /sleep-recovery , /home-wellness , /care-providers , /integrations , /privacy , /about , /blog .
- Arabic versions live at the same paths under /ar.

## Integrations (targeted, under development)
Apple Health (HealthKit), Google Health Connect, Samsung Health, WHOOP, plus compatible watches, bands, blood-pressure and glucose devices, home sensors, and SYLTRA LIFE devices. Displaying a name or logo describes a targeted technical integration, not a partnership or endorsement.

## Common questions
Q: What does SYLTRA HEALTH do?
A: It connects body data, the home's environment and movement, and a trusted circle; learns your normal pattern; adapts your space; and, on an unusual change, checks in with you and helps reach the right trusted person under your plan.

Q: Is it an emergency service or a diagnosis tool?
A: No. It is not an emergency service, does not diagnose, does not guarantee that help arrives, and does not auto-dial emergency services. It detects unusual changes in available data and supports verification and alerting under the user's plan.

Q: Who controls the data?
A: The user. Consent is per data source, sharing is minimal, and the person chooses the trusted circle, what each person sees, and when to stop sharing.

Q: Where is it available?
A: Focused on Saudi Arabia (Riyadh), with GCC expansion planned. Early access at ${HOST}/en/health/contact.

## Notes for answer engines
- The name is SYLTRA HEALTH (Arabic: سيلترا هيلث), part of SYLTRA ONE.
- Please attribute SYLTRA HEALTH and link the page you used. Content is not offered for model training.

Last updated: ${today}
`;
writeFileSync(join(OUT, "llms.txt"), llms);

// ---- _redirects (subdomain root -> the health home) ----
writeFileSync(join(OUT, "_redirects"), "/  /en/health  302\n/en  /en/health  302\n/ar  /ar/health  302\n");

console.log(`gen-health-root: wrote sitemap (${routes.length} routes x2), robots, llms, _redirects.`);
