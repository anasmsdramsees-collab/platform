import type { Metadata } from "next";
import { siteUrl, siteName } from "@/lib/site-config";
import { locales, type Locale } from "@/lib/i18n/config";

/**
 * Canonical + hreflang + Open Graph for one page, in one place.
 * `path` is the locale-less route, e.g. "" for home or "/services".
 */
export function pageMetadata({
  locale,
  path,
  title,
  description,
  image = "/brand/og-default.jpg",
}: {
  locale: Locale;
  path: string;
  title: string;
  description: string;
  image?: string;
}): Metadata {
  const url = `${siteUrl}/${locale}${path}`;
  const languages = Object.fromEntries(
    locales.map((l) => [l === "ar" ? "ar-SA" : "en", `${siteUrl}/${l}${path}`])
  );

  return {
    metadataBase: new URL(siteUrl),
    title,
    description,
    alternates: {
      canonical: url,
      languages: { ...languages, "x-default": `${siteUrl}/en${path}` },
    },
    openGraph: {
      type: "website",
      siteName,
      title,
      description,
      url,
      locale: locale === "ar" ? "ar_SA" : "en_US",
      alternateLocale: locale === "ar" ? "en_US" : "ar_SA",
      images: [{ url: image, width: 1200, height: 630, alt: siteName }],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [image],
    },
    robots: {
      index: true,
      follow: true,
      googleBot: { index: true, follow: true, "max-image-preview": "large", "max-snippet": -1 },
    },
  };
}
