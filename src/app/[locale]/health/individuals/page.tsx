import type { Metadata } from "next";
import { isLocale, type Locale } from "@/lib/i18n/config";
import { healthMetadata } from "@/lib/health-meta";
import HealthPageView from "@/components/health/health-page-view";

const KEY = "individuals";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  return healthMetadata(KEY, locale);
}

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  return <HealthPageView slugKey={KEY} locale={locale} />;
}
