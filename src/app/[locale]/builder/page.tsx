import type { Metadata } from "next";
import { locales, isLocale, type Locale } from "@/lib/i18n/config";
import { pageMetadata } from "@/lib/seo";
import { Builder } from "@/components/builder/builder";

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

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
    path: "/builder",
    title: ar
      ? "ابنِ بيتك الذكي | تجربة تفاعلية ثلاثية الأبعاد | سيلترا وان"
      : "Build Your Smart Home | Interactive 3D Experience | Syltra One",
    description: ar
      ? "اختر فيلا أو شقة أو مكتب، ركّب الإضاءة والستائر والتكييف والأقفال والكاميرات، وشغّلها من لوحة تحكم حية في تجربة ثلاثية الأبعاد."
      : "Pick a villa, apartment or office, add lighting, curtains, climate, locks and cameras, then run them from a live control panel in 3D.",
  });
}

export default async function BuilderPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  return <Builder locale={locale} />;
}
