import type { Metadata } from "next";
import { isLocale, type Locale } from "@/lib/i18n/config";
import AdminDashboard from "@/components/health/admin/admin-dashboard";

export const metadata: Metadata = {
  title: "Dashboard | SYLTRA HEALTH Admin",
  robots: { index: false, follow: false },
};

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  return <AdminDashboard locale={locale} />;
}
