"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Locale } from "@/lib/i18n/config";
import { siteUrl } from "@/lib/site-config";
import { HEALTH, HEALTH_BRAND, HEALTH_NAV, HEALTH_SOCIAL } from "@/lib/health-content";
import HealthLogo from "./health-logo";

export default function HealthFooter({ locale }: { locale: Locale }) {
  const pathname = usePathname() || "";
  if (pathname.includes("/health/admin")) return null;

  const ar = locale === "ar";
  const year = new Date().getFullYear();
  const base = `/${locale}/health`;
  const linkCls = "text-sm text-chrome-dim transition-colors hover:text-platinum";

  const navLabel = (h: string) => {
    const n = HEALTH_NAV.find((x) => x.href === h);
    return n ? (ar ? n.label.ar : n.label.en) : h;
  };
  const lnk = (h: string) => ({ label: navLabel(h), href: h === "" ? base : `${base}${h}`, external: false });
  const columns: { title: { ar: string; en: string }; links: { label: string; href: string; external: boolean }[] }[] = [
    {
      title: { ar: "المنصّة", en: "Platform" },
      links: [lnk(""), lnk("/how-it-works"), lnk("/app"), lnk("/integrations"), lnk("/medication")],
    },
    {
      title: { ar: "لمن", en: "For You" },
      links: [lnk("/individuals"), lnk("/older-adults"), lnk("/chronic-conditions"), lnk("/sleep-recovery"), lnk("/home-wellness"), lnk("/accessibility"), lnk("/care-providers")],
    },
    {
      title: { ar: "الشركة", en: "Company" },
      links: [lnk("/about"), lnk("/blog"), lnk("/privacy"), { label: ar ? "تواصل معنا" : "Contact", href: `${base}/contact`, external: false }],
    },
    {
      title: { ar: "تابعنا", en: "Follow" },
      links: [
        ...HEALTH_SOCIAL.map((s) => ({ label: s.name, href: s.href, external: true })),
        { label: "info@syltraone.com", href: "mailto:info@syltraone.com", external: true },
      ],
    },
  ];

  return (
    <footer className="border-t border-hairline">
      {/* Permanent trust line */}
      <div className="border-b border-hairline" style={{ background: `rgba(${HEALTH.rgb},0.04)` }}>
        <div className="mx-auto max-w-6xl px-5 py-5 sm:px-8">
          <p className="text-center text-[13px] leading-relaxed text-chrome-dim">
            {ar ? HEALTH_BRAND.trustLine.ar : HEALTH_BRAND.trustLine.en}
          </p>
        </div>
      </div>

      {/* Sitemap columns (Apple-style) */}
      <div className="mx-auto max-w-6xl px-5 py-12 sm:px-8 sm:py-14">
        <div className="grid grid-cols-2 gap-x-8 gap-y-10 sm:grid-cols-3 lg:grid-cols-4">
          {columns.map((col) => (
            <div key={col.title.en}>
              <p className="font-mono text-[11px] uppercase tracking-widest text-slate">{ar ? col.title.ar : col.title.en}</p>
              <div className="mt-4 grid gap-2.5">
                {col.links.map((l) =>
                  l.external ? (
                    <a key={l.label} href={l.href} target="_blank" rel="noopener noreferrer" className={linkCls}>
                      {l.label}
                    </a>
                  ) : (
                    <Link key={l.label} href={l.href} className={linkCls}>
                      {l.label}
                    </Link>
                  )
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Brand row */}
        <div className="mt-12 flex flex-col items-start gap-4 border-t border-hairline pt-8 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <HealthLogo locale={locale} />
            <span className="font-mono text-[12px] text-slate">{ar ? HEALTH_BRAND.tagline.ar : HEALTH_BRAND.tagline.en}</span>
          </div>
          <Link href={`/${locale}`} className="text-[12.5px] text-chrome-dim transition-colors hover:text-platinum">
            {ar ? HEALTH_BRAND.endorsement.ar : HEALTH_BRAND.endorsement.en} ↗
          </Link>
        </div>
      </div>

      <div className="mx-auto max-w-6xl px-5 pb-10 sm:px-8">
        <p className="text-[12px] leading-relaxed text-slate">
          {ar
            ? "المعلومات والخدمات المعروضة مخصصة لدعم الرفاه وتنظيم البيانات والمتابعة العامة. لا تمثل تشخيصاً أو علاجاً ولا تستبدل استشارة المختص أو خدمات الطوارئ."
            : "Information and services are intended to support wellness, data organization and general follow-up. They do not provide diagnosis or treatment and do not replace professional advice or emergency services."}
        </p>
        <p className="mt-4 font-mono text-[11px] text-slate">
          © {year} SYLTRA HEALTH · {ar ? "إحدى شركات سيلترا وان" : "A SYLTRA ONE Company"} ·{" "}
          <Link href={`/${locale}`} className="transition-colors hover:text-platinum">{siteUrl.replace("https://", "")}</Link>
        </p>
      </div>
    </footer>
  );
}
