import type { MetadataRoute } from "next";
import { siteUrl } from "@/lib/site-config";
import { locales } from "@/lib/i18n/config";
import { productCatalog } from "@/lib/products";
import { landings } from "@/lib/landing";
import { DIVISIONS } from "@/lib/divisions";
import { DIVISION_CONTENT } from "@/lib/division-content";

// Static export needs these emitted at build time.
export const dynamic = "force-static";


// Static routes, listed once and emitted for every locale with hreflang siblings.
const ROUTES: { path: string; priority: number; changeFrequency: MetadataRoute.Sitemap[number]["changeFrequency"] }[] = [
  { path: "", priority: 1, changeFrequency: "weekly" },
  { path: "/products", priority: 0.9, changeFrequency: "weekly" },
  { path: "/store", priority: 0.9, changeFrequency: "weekly" },
  { path: "/solutions", priority: 0.8, changeFrequency: "monthly" },
  { path: "/services", priority: 0.8, changeFrequency: "monthly" },
  { path: "/apps", priority: 0.7, changeFrequency: "monthly" },
  { path: "/about", priority: 0.7, changeFrequency: "monthly" },
  { path: "/faq", priority: 0.6, changeFrequency: "monthly" },
  { path: "/contact", priority: 0.6, changeFrequency: "yearly" },
  { path: "/quote", priority: 0.9, changeFrequency: "monthly" },
  { path: "/builder", priority: 0.9, changeFrequency: "monthly" },
  { path: "/sitemap", priority: 0.4, changeFrequency: "weekly" },
];

function languagesFor(path: string) {
  return Object.fromEntries(locales.map((l) => [l, `${siteUrl}/${l}${path}`]));
}

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date();
  const entries: MetadataRoute.Sitemap = [];

  for (const route of ROUTES) {
    for (const locale of locales) {
      entries.push({
        url: `${siteUrl}/${locale}${route.path}`,
        lastModified,
        changeFrequency: route.changeFrequency,
        priority: route.priority,
        alternates: { languages: languagesFor(route.path) },
      });
    }
  }

  // Division pages + their service detail pages.
  for (const division of DIVISIONS) {
    for (const locale of locales) {
      entries.push({
        url: `${siteUrl}/${locale}${division.href}`,
        lastModified,
        changeFrequency: "weekly",
        priority: 0.9,
        alternates: { languages: languagesFor(division.href) },
      });
    }
    const content = DIVISION_CONTENT[division.key as keyof typeof DIVISION_CONTENT];
    if (content) {
      for (const s of content.systems) {
        if (!s.slug) continue;
        const path = `${division.href}/${s.slug}`;
        for (const locale of locales) {
          entries.push({
            url: `${siteUrl}/${locale}${path}`,
            lastModified,
            changeFrequency: "monthly",
            priority: 0.8,
            alternates: { languages: languagesFor(path) },
          });
        }
      }
    }
  }

  for (const landing of landings) {
    const path = `/l/${landing.slug}`;
    for (const locale of locales) {
      entries.push({
        url: `${siteUrl}/${locale}${path}`,
        lastModified,
        changeFrequency: "monthly",
        priority: 0.9,
        alternates: { languages: languagesFor(path) },
      });
    }
  }

  for (const category of productCatalog) {
    for (const product of category.items) {
      const path = `/products/${product.slug}`;
      for (const locale of locales) {
        entries.push({
          url: `${siteUrl}/${locale}${path}`,
          lastModified,
          changeFrequency: "monthly",
          priority: 0.7,
          alternates: { languages: languagesFor(path) },
        });
      }
    }
  }

  return entries;
}
