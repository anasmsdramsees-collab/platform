import { isLocale, type Locale } from "@/lib/i18n/config";
import HealthNav from "@/components/health/health-nav";
import HealthFooter from "@/components/health/health-footer";
import { HealthThemeScope } from "@/components/health/health-theme";
import HealthSila from "@/components/health/health-sila";

export default async function HealthLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  return (
    <HealthThemeScope>
      <HealthNav locale={locale} />
      <div className="flex-1">{children}</div>
      <HealthFooter locale={locale} />
      <HealthSila locale={locale} />
    </HealthThemeScope>
  );
}
