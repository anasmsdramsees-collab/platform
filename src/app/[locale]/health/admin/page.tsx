import type { Metadata } from "next";
import { isLocale, type Locale } from "@/lib/i18n/config";
import AdminLogin from "@/components/health/admin/admin-login";

export const metadata: Metadata = {
  title: "Admin Console | SYLTRA HEALTH",
  robots: { index: false, follow: false },
};

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  return <AdminLogin locale={locale} />;
}
