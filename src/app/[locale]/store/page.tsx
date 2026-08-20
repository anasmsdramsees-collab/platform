import { locales, isLocale, type Locale } from "@/lib/i18n/config";
import StoreClient from "@/components/store-client";

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
