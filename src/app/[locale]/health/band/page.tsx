import type { Metadata } from "next";
import { isLocale, type Locale } from "@/lib/i18n/config";
import { pageMetadata } from "@/lib/seo";
import { healthUrl } from "@/lib/site-config";
import HealthBandPage from "@/components/health/health-band-page";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const ar = locale === "ar";
  return pageMetadata({
    locale,
    path: "/health/band",
    title: ar ? "سوار سيلترا هيلث | مؤشرات صحتك بهدوء" : "SYLTRA HEALTH Band | Your signals, quietly",
    description: ar
      ? "سوار بلا شاشة يجمع مؤشرات القلب والأكسجين والنوم والنشاط والتعافي وصحة المرأة في صورة واحدة واضحة، متصل بمنزلك ومساعِدتك سيلا."
      : "A screenless band that brings heart, oxygen, sleep, activity, recovery and women's health into one clear picture, connected to your home and SILA.",
    image: "/brand/health-og.jpg",
    baseUrl: healthUrl,
  });
}

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  return <HealthBandPage locale={locale} />;
}
