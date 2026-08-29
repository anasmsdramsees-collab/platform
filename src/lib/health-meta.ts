import type { Metadata } from "next";
import type { Locale } from "@/lib/i18n/config";
import { pageMetadata } from "@/lib/seo";
import { healthUrl } from "@/lib/site-config";
import { HEALTH_PAGES } from "@/lib/health-pages";
import { pickH } from "@/lib/health-content";

/** Metadata for one HEALTH page, keyed by its locale-less slug ("" = home). */
export function healthMetadata(slugKey: string, locale: Locale): Metadata {
  const page = HEALTH_PAGES[slugKey];
  return pageMetadata({
    locale,
    path: `/health${page.slug}`,
    title: pickH(page.seoTitle, locale),
    description: pickH(page.seoDescription, locale),
    image: "/brand/og-default.jpg",
    baseUrl: healthUrl,
  });
}
