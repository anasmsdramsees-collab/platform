import type { Metadata } from "next";
import Link from "next/link";
import { isLocale, type Locale } from "@/lib/i18n/config";
import { pageMetadata } from "@/lib/seo";
import { DIVISIONS, divisionName } from "@/lib/divisions";
import { DIVISION_CONTENT, pick } from "@/lib/division-content";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const title = locale === "ar" ? "خريطة الموقع | سيلترا وان" : "Sitemap | Syltra One";
  const description =
    locale === "ar"
      ? "كل صفحات سيلترا وان في مكان واحد — الأقسام والخدمات وصفحات الشركة."
      : "Every Syltra One page in one place — divisions, services and company pages.";
  return pageMetadata({ locale, path: "/sitemap", title, description });
}

export default async function SitemapPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const ar = locale === "ar";

  const company = [
    { href: `/${locale}`, label: ar ? "الرئيسية — سيلترا وان" : "Home — Syltra One" },
    { href: `/${locale}/about`, label: ar ? "من نحن" : "About" },
    { href: `/${locale}/contact`, label: ar ? "تواصل معنا" : "Contact" },
    { href: `/${locale}/quote`, label: ar ? "احجز معاينة" : "Book a survey" },
  ];

  const lifePages = [
    { href: `/${locale}/life`, label: ar ? "سيلترا لايف — المنزل الذكي" : "Syltra Life — Smart home" },
    { href: `/${locale}/products`, label: ar ? "المنتجات" : "Products" },
    { href: `/${locale}/store`, label: ar ? "المتجر" : "Store" },
    { href: `/${locale}/builder`, label: ar ? "ابنِ بيتك" : "Build your home" },
    { href: `/${locale}/solutions`, label: ar ? "الحلول" : "Solutions" },
    { href: `/${locale}/services`, label: ar ? "الخدمات" : "Services" },
    { href: `/${locale}/apps`, label: ar ? "التطبيقات" : "Apps" },
    { href: `/${locale}/faq`, label: ar ? "الأسئلة الشائعة" : "FAQ" },
  ];

  const linkCls = "block py-1.5 text-sm text-chrome-dim transition-colors hover:text-platinum";

  return (
    <div className="mx-auto max-w-6xl px-5 py-24 sm:px-8">
      <p className="font-mono text-[12px] uppercase tracking-[0.14em] text-slate">
        {ar ? "خريطة الموقع" : "Sitemap"}
      </p>
      <h1 className="font-display mt-3 text-balance text-4xl font-bold text-platinum sm:text-5xl">
        {ar ? "كل الصفحات في مكان واحد." : "Every page in one place."}
      </h1>

      {/* Divisions with their services */}
      <div className="mt-14 grid grid-cols-1 gap-x-10 gap-y-12 sm:grid-cols-2 lg:grid-cols-3">
        {DIVISIONS.map((d) => {
          const content = DIVISION_CONTENT[d.key as keyof typeof DIVISION_CONTENT];
          const services = content?.systems.filter((s) => s.slug) ?? [];
          return (
            <div key={d.key}>
              <div className="flex items-center gap-2.5 border-b border-hairline pb-3">
                <span className="h-2.5 w-2.5 flex-none rounded-full" style={{ background: d.color }} aria-hidden />
                <Link href={`/${locale}${d.href}`} className="font-display text-lg font-bold text-platinum transition-opacity hover:opacity-80">
                  {divisionName(d, locale)}
                </Link>
              </div>
              <div className="mt-3">
                {services.length ? (
                  services.map((s) => (
                    <Link key={s.slug} href={`/${locale}${d.href}/${s.slug}`} className={linkCls}>
                      {pick(s.title, locale)}
                    </Link>
                  ))
                ) : (
                  <Link href={`/${locale}${d.href}`} className={linkCls}>
                    {ar ? "زيارة القسم" : "Visit division"}
                  </Link>
                )}
              </div>
            </div>
          );
        })}

        {/* Company */}
        <div>
          <div className="border-b border-hairline pb-3">
            <p className="font-display text-lg font-bold text-platinum">{ar ? "الشركة" : "Company"}</p>
          </div>
          <div className="mt-3">
            {company.map((l) => (
              <Link key={l.href} href={l.href} className={linkCls}>
                {l.label}
              </Link>
            ))}
          </div>
        </div>

        {/* Life pages */}
        <div>
          <div className="border-b border-hairline pb-3">
            <p className="font-display text-lg font-bold text-platinum">{ar ? "سيلترا لايف" : "Syltra Life"}</p>
          </div>
          <div className="mt-3">
            {lifePages.map((l) => (
              <Link key={l.href} href={l.href} className={linkCls}>
                {l.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
