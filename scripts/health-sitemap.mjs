#!/usr/bin/env node
/**
 * Health-site sitemap + robots generator.
 *
 * The SYLTRA HEALTH Cloudflare Pages project builds from the same `out/` as the
 * main site, whose own sitemap intentionally excludes /health. This script runs
 * only in the HEALTH project's build command and OVERWRITES out/sitemap.xml and
 * out/robots.txt so the health subdomain advertises its own pages on
 * health.syltraone.com. It never runs for the main syltraone.com build.
 *
 * It works by scanning the already-built out/{en,ar}/health tree, so it stays in
 * sync with the pages without importing any TS route data.
 */
import { readdirSync, statSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const BASE = "https://health.syltraone.com";
const OUT = "out";
const LOCALES = ["en", "ar"];

/** Collect every directory under out/<locale>/health that has an index.html. */
function collectPaths(locale) {
  const root = join(OUT, locale, "health");
  const paths = [];
  const walk = (dir, rel) => {
    let entries;
    try {
      entries = readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    if (entries.some((e) => e.isFile() && e.name === "index.html")) {
      paths.push(rel); // rel is the locale-less path under /health, "" = home
    }
    for (const e of entries) {
      if (e.isDirectory() && !e.name.startsWith("_") && !e.name.startsWith("[")) {
        walk(join(dir, e.name), rel ? `${rel}/${e.name}` : e.name);
      }
    }
  };
  walk(root, "");
  return paths;
}

// The /admin area is private tooling — keep it out of the sitemap.
const EXCLUDE = new Set(["admin"]);

// Union of paths across locales (both locales exist for every page).
const pathSet = new Set();
for (const l of LOCALES) for (const p of collectPaths(l)) pathSet.add(p);
const paths = [...pathSet].filter((p) => !EXCLUDE.has(p.split("/")[0])).sort();

const url = (locale, p) => `${BASE}/${locale}/health${p ? `/${p}` : ""}/`;

const now = new Date().toISOString();
const entries = paths
  .map((p) => {
    const alts = LOCALES.map(
      (l) => `    <xhtml:link rel="alternate" hreflang="${l === "ar" ? "ar-SA" : "en"}" href="${url(l, p)}"/>`
    ).join("\n");
    const xdefault = `    <xhtml:link rel="alternate" hreflang="x-default" href="${url("en", p)}"/>`;
    // Emit one <url> per locale, each carrying the full alternate set.
    return LOCALES.map(
      (l) =>
        `  <url>\n    <loc>${url(l, p)}</loc>\n    <lastmod>${now}</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>${p === "" ? "1.0" : "0.8"}</priority>\n${alts}\n${xdefault}\n  </url>`
    ).join("\n");
  })
  .join("\n");

const sitemap = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n${entries}\n</urlset>\n`;

writeFileSync(join(OUT, "sitemap.xml"), sitemap);

const robots = `User-Agent: *
Allow: /
Disallow: /en/health/admin
Disallow: /ar/health/admin

User-Agent: OAI-SearchBot
Allow: /

User-Agent: ChatGPT-User
Allow: /

User-Agent: Claude-SearchBot
Allow: /

User-Agent: Claude-User
Allow: /

User-Agent: PerplexityBot
Allow: /

User-Agent: Applebot
Allow: /

User-Agent: Bingbot
Allow: /

Host: ${BASE}
Sitemap: ${BASE}/sitemap.xml
`;

writeFileSync(join(OUT, "robots.txt"), robots);

console.log(`health-sitemap: wrote ${paths.length} pages (${paths.length * LOCALES.length} URLs) + robots.txt for ${BASE}`);
