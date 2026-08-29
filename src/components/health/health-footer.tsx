import Link from "next/link";
import type { Locale } from "@/lib/i18n/config";
import { siteUrl } from "@/lib/site-config";
import { HEALTH, HEALTH_BRAND, HEALTH_NAV } from "@/lib/health-content";
import HealthLogo from "./health-logo";

export default function HealthFooter({ locale }: { locale: Locale }) {
  const ar = locale === "ar";
  const year = new Date().getFullYear();
  const base = `/${locale}/health`;
  const linkCls = "text-sm text-chrome-dim transition-colors hover:text-platinum";

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

      <div className="mx-auto grid max-w-6xl gap-10 px-5 py-14 sm:px-8 md:grid-cols-[1.2fr_1fr_1fr]">
        <div className="max-w-xs">
          <HealthLogo locale={locale} />
          <p className="mt-4 font-mono text-[12.5px] text-slate">
            {ar ? HEALTH_BRAND.tagline.ar : HEALTH_BRAND.tagline.en}
          </p>
          <Link href={`/${locale}`} className="mt-4 inline-block text-[12.5px] text-chrome-dim transition-colors hover:text-platinum">
            {ar ? HEALTH_BRAND.endorsement.ar : HEALTH_BRAND.endorsement.en} ↗
          </Link>
        </div>

        <div>
          <p className="font-mono text-[11px] uppercase tracking-widest text-slate">{ar ? "الأقسام" : "Sections"}</p>
          <div className="mt-3 grid gap-2">
            {HEALTH_NAV.slice(0, 7).map((n) => (
              <Link key={n.href} href={n.href === "" ? base : `${base}${n.href}`} className={linkCls}>
                {ar ? n.label.ar : n.label.en}
              </Link>
            ))}
          </div>
        </div>

        <div>
          <p className="font-mono text-[11px] uppercase tracking-widest text-slate">{ar ? "روابط" : "More"}</p>
          <div className="mt-3 grid gap-2">
            {HEALTH_NAV.slice(7).map((n) => (
              <Link key={n.href} href={n.href === "" ? base : `${base}${n.href}`} className={linkCls}>
                {ar ? n.label.ar : n.label.en}
              </Link>
            ))}
            <Link href={`${base}/contact`} className={linkCls}>{ar ? "تواصل معنا" : "Contact"}</Link>
            <a href="mailto:info@syltraone.com" className={linkCls}>info@syltraone.com</a>
          </div>
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
