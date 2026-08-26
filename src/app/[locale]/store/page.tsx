import { locales, isLocale, type Locale } from "@/lib/i18n/config";
import StoreClient from "@/components/store-client";

import type { Metadata } from "next";
import { pageMetadata } from "@/lib/seo";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: rawLocale } = await params;
  const locale: Locale = isLocale(rawLocale) ? rawLocale : "en";
  return pageMetadata({
    locale,
    path: "/store",
    title: locale === "ar" ? "متجر سيلترا | سيلترا لايف" : "Syltra Store | Syltra Life",
    description:
      locale === "ar"
        ? "اطلب أجهزة المنزل الذكي والأمان والأقفال وكاميرات المراقبة وأنظمة الصوت من سيلترا لايف، مع التوصيل والتركيب داخل الرياض."
        : "Order smart home, security, lock, CCTV and audio devices from Syltra Life, with delivery and installation in Riyadh.",
  });
}

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export default async function StorePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: rawLocale } = await params;
  const locale: Locale = isLocale(rawLocale) ? rawLocale : "en";
  return <StoreClient locale={locale} />;
}
