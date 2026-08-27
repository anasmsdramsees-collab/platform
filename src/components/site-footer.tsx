"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Locale } from "@/lib/i18n/config";
import type { Dictionary } from "@/lib/i18n/dictionary";
import { DIVISIONS, divisionName } from "@/lib/divisions";
import Logo from "./logo";
import { assetPath } from "@/lib/base-path";

const LIFE_SEGMENTS = new Set([
  "life",
  "products",
  "store",
  "builder",
  "solutions",
  "services",
  "apps",
  "quote",
]);

export default function SiteFooter({ locale, dict }: { locale: Locale; dict: Dictionary }) {
  const year = new Date().getFullYear();
  const pathname = usePathname() || `/${locale}`;
  const seg = pathname.replace(/^\/(en|ar)/, "").split("/").filter(Boolean)[0] || "";
  const isLife = LIFE_SEGMENTS.has(seg);

  const linkCls =
    "mt-2 block text-sm text-chrome-dim transition-colors hover:text-platinum";
  const headCls = "font-mono text-[11px] uppercase tracking-widest text-slate";

  return (
    <footer className="border-t border-hairline">
      <div className="mx-auto flex max-w-6xl flex-col gap-10 px-5 py-14 sm:px-8 md:flex-row md:items-start md:justify-between">
        <div className="max-w-xs">
          <Logo locale={locale} />
          <p className="mt-4 font-mono text-[12.5px] text-slate">{dict.footer.tagline}</p>
        </div>

        {isLife ? (
          /* ---- Life footer (the smart-home world) ---- */
          <div className="grid grid-cols-2 gap-10 sm:grid-cols-4">
            <div>
              <p className={headCls}>{dict.footer.products}</p>
              <Link href={`/${locale}/products`} className={`mt-3 block text-sm text-chrome-dim transition-colors hover:text-platinum`}>{dict.nav.products}</Link>
              <Link href={`/${locale}/store`} className={linkCls}>{dict.nav.store}</Link>
              <Link href={`/${locale}/solutions`} className={linkCls}>{dict.nav.solutions}</Link>
              <Link href={`/${locale}/services`} className={linkCls}>{dict.nav.services}</Link>
            </div>
            <div>
              <p className={headCls}>{dict.footer.apps}</p>
              <Link href={`/${locale}/apps`} className={`mt-3 block text-sm text-chrome-dim transition-colors hover:text-platinum`}>Syltra TV</Link>
              <Link href={`/${locale}/apps`} className={linkCls}>{locale === "ar" ? "سيلترا هوم" : "Syltra Home"}</Link>
            </div>
            <div>
              <p className={headCls}>{dict.footer.company}</p>
              <Link href={`/${locale}/about`} className={`mt-3 block text-sm text-chrome-dim transition-colors hover:text-platinum`}>{dict.nav.about}</Link>
              <Link href={`/${locale}/faq`} className={linkCls}>{dict.nav.faq}</Link>
            </div>
            <div>
              <p className={headCls}>{dict.footer.contact}</p>
              <Link href={`/${locale}/contact`} className={`mt-3 block text-sm text-chrome-dim transition-colors hover:text-platinum`}>{dict.nav.contact}</Link>
              <Link href={`/${locale}/quote`} className={linkCls}>{dict.nav.quote}</Link>
              <a href="https://www.instagram.com/syltrahome/" target="_blank" rel="noopener noreferrer" className={linkCls}>Instagram</a>
              <a href="https://www.tiktok.com/@syltra.home" target="_blank" rel="noopener noreferrer" className={linkCls}>TikTok</a>
              <a href="https://wa.me/966550098550" target="_blank" rel="noopener noreferrer" className={linkCls}>WhatsApp</a>
            </div>
          </div>
        ) : (
          /* ---- Umbrella / division footer (the group) ---- */
          <div className="grid grid-cols-2 gap-10 sm:grid-cols-3">
            <div>
              <p className={headCls}>{locale === "ar" ? "الأقسام" : "Divisions"}</p>
              {DIVISIONS.map((d, i) => (
                <Link
                  key={d.key}
                  href={`/${locale}${d.href}`}
                  className={i === 0 ? "mt-3 block text-sm text-chrome-dim transition-colors hover:text-platinum" : linkCls}
                >
                  {divisionName(d, locale)}
                </Link>
              ))}
            </div>
            <div>
              <p className={headCls}>{dict.footer.company}</p>
              <Link href={`/${locale}/about`} className={`mt-3 block text-sm text-chrome-dim transition-colors hover:text-platinum`}>{dict.nav.about}</Link>
              <Link href={`/${locale}/contact`} className={linkCls}>{dict.nav.contact}</Link>
            </div>
            <div>
              <p className={headCls}>{dict.footer.contact}</p>
              <a href="https://wa.me/966550098550" target="_blank" rel="noopener noreferrer" className={`mt-3 block text-sm text-chrome-dim transition-colors hover:text-platinum`}>WhatsApp</a>
              <a href="tel:0550098550" className={linkCls}>0550098550</a>
            </div>
          </div>
        )}
      </div>

      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-5 pb-10 sm:flex-row sm:items-center sm:justify-between sm:px-8">
        <p className="font-mono text-[11px] text-slate">
          © {year} Syltra One®. {dict.footer.rights}
        </p>
        <div className="flex items-center gap-3">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={assetPath("/brand/vision-2030.png")}
            alt={locale === "ar" ? "رؤية 2030 · المملكة العربية السعودية" : "Saudi Vision 2030"}
            className="h-9 w-auto opacity-90"
          />
          <span className="text-[11px] text-slate">
            {locale === "ar" ? "داعمون لرؤية المملكة 2030" : "Aligned with Saudi Vision 2030"}
          </span>
        </div>
      </div>
    </footer>
  );
}
