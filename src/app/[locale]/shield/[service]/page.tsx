import type { Metadata } from "next";
import { isLocale, type Locale } from "@/lib/i18n/config";
import { locales } from "@/lib/i18n/config";
import { pageMetadata } from "@/lib/seo";
import { DIVISION_CONTENT, pick } from "@/lib/division-content";
import { DIVISIONS, divisionName } from "@/lib/divisions";
import ServiceDetail, { findService } from "@/components/service-detail";

const DIVISION = "shield" as const;
const division = DIVISIONS.find((d) => d.key === DIVISION)!;

export function generateStaticParams() {
  const slugs = DIVISION_CONTENT[DIVISION].systems.filter((s) => s.slug).map((s) => s.slug!);
  return locales.flatMap((locale) => slugs.map((service) => ({ locale, service })));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; service: string }>;
}): Promise<Metadata> {
  const { locale: raw, service } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const found = findService(DIVISION, service);
  if (!found) return {};
  const name = divisionName(division, locale);
  const title = `${pick(found.service.title, locale)} | ${name}`;
  const description = found.service.lead ? pick(found.service.lead, locale) : title;
  const geo = locale === "ar" ? ["السعودية", "الرياض"] : ["Saudi Arabia", "Riyadh"];
  const keywords = [
    found.service.title.ar,
    found.service.title.en,
    found.service.en,
    name,
    locale === "ar" ? division.label.ar : division.label.en,
    ...geo,
  ].filter(Boolean) as string[];
  return pageMetadata({ locale, path: `${division.href}/${service}`, title, description, keywords });
}

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string; service: string }>;
}) {
  const { locale: raw, service } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  return <ServiceDetail divisionKey={DIVISION} slug={service} locale={locale} />;
}
