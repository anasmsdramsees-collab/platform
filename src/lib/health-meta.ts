import type { Metadata } from "next";
import type { Locale } from "@/lib/i18n/config";
import { pageMetadata } from "@/lib/seo";
import { healthUrl } from "@/lib/site-config";
import { HEALTH_PAGES } from "@/lib/health-pages";
import { pickH } from "@/lib/health-content";

const BASE_KEYWORDS: Record<Locale, string[]> = {
  en: [
    "SYLTRA HEALTH",
    "connected health",
    "smart home health",
    "health integrations",
    "wearables health data",
    "Apple Health",
    "Samsung Health",
    "Google Health Connect",
    "WHOOP",
    "Fitbit",
    "home sensors health",
    "health and wellness technology",
    "Saudi Arabia",
    "Riyadh",
  ],
  ar: [
    "سيلترا هيلث",
    "الصحة المتصلة",
    "صحة المنزل الذكي",
    "تكاملات صحية",
    "الأجهزة القابلة للارتداء",
    "حساسات المنزل",
    "تقنيات الصحة والرفاه",
    "المملكة العربية السعودية",
    "الرياض",
  ],
};

/** Metadata for one HEALTH page, keyed by its locale-less slug ("" = home). */
export function healthMetadata(slugKey: string, locale: Locale): Metadata {
  const page = HEALTH_PAGES[slugKey];
  // Branded share card (SYLTRA HEALTH mark) for all marketing pages.
  const image = "/brand/health-og.jpg";
  const titleWords = pickH(page.seoTitle, locale)
    .replace(/[|,.]/g, " ")
    .split(/\s+/)
    .filter((w) => w.length > 2)
    .slice(0, 6);

  return pageMetadata({
    locale,
    path: `/health${page.slug}`,
    title: pickH(page.seoTitle, locale),
    description: pickH(page.seoDescription, locale),
    image,
    baseUrl: healthUrl,
    keywords: [...new Set([...titleWords, ...BASE_KEYWORDS[locale]])],
  });
}
