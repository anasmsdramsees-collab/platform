import type { Metadata } from "next";
import { isLocale, type Locale } from "@/lib/i18n/config";
import { pageMetadata } from "@/lib/seo";
import { DIVISIONS, divisionName } from "@/lib/divisions";
import { DIVISION_CONTENT, pick } from "@/lib/division-content";
import DivisionPage from "@/components/division-page";

const KEY = "os" as const;
const division = DIVISIONS.find((d) => d.key === KEY)!;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const c = DIVISION_CONTENT[KEY];
  return pageMetadata({
    locale,
    path: division.href,
    title: `${divisionName(division, locale)} | ${pick(c.h1, locale)}`,
    description: pick(c.intro, locale),
  });
}

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  return <DivisionPage division={division} locale={locale} />;
}
