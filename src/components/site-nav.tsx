"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutGrid, Info, Mail, ShoppingBag, Home, ChevronDown } from "lucide-react";
import type { Locale } from "@/lib/i18n/config";
import type { Dictionary } from "@/lib/i18n/dictionary";
import { DIVISIONS, divisionName } from "@/lib/divisions";
import Logo from "./logo";
import { LimelightNav, type NavItem } from "./limelight-nav";

export default function SiteNav({ locale, dict }: { locale: Locale; dict: Dictionary }) {
  const pathname = usePathname() || `/${locale}`;
  const rest = pathname.replace(/^\/(en|ar)/, "") || "";
  const otherLocale: Locale = locale === "en" ? "ar" : "en";
  const otherHref = `/${otherLocale}${rest}`;
  const [divOpen, setDivOpen] = useState(false);

  const divisionsLabel = locale === "ar" ? "الأقسام" : "Divisions";

  // Umbrella-level primary nav. Life's own sub-pages (products, store, builder,
  // solutions, services, apps) live inside /life, reached from that division.
  const links = [
    { href: `/${locale}/store`, label: dict.nav.store },
    { href: `/${locale}/about`, label: dict.nav.about },
    { href: `/${locale}/contact`, label: dict.nav.contact },
  ];

  const mobileNavItems: NavItem[] = [
    { id: "divisions", icon: <LayoutGrid />, label: divisionsLabel, href: `/${locale}#divisions` },
    { id: "life", icon: <Home />, label: locale === "ar" ? "لايف" : "Life", href: `/${locale}/life` },
    { id: "store", icon: <ShoppingBag />, label: dict.nav.store, href: `/${locale}/store` },
    { id: "about", icon: <Info />, label: dict.nav.about, href: `/${locale}/about` },
    { id: "contact", icon: <Mail />, label: dict.nav.contact, href: `/${locale}/contact` },
  ];
  const mobileActiveIndex = mobileNavItems.findIndex((item) => pathname.startsWith(item.href!.split("#")[0]));

  return (
    <>
      <header className="sticky top-0 z-40 border-b border-hairline bg-void/85 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-5 py-4 sm:px-8">
          <Logo locale={locale} />
          <nav className="hidden items-center gap-5 lg:flex lg:gap-7">
            {/* Divisions dropdown */}
            <div
              className="relative"
              onMouseEnter={() => setDivOpen(true)}
              onMouseLeave={() => setDivOpen(false)}
            >
              <button
                type="button"
                aria-haspopup="true"
                aria-expanded={divOpen}
                onClick={() => setDivOpen((v) => !v)}
                className="flex items-center gap-1.5 font-mono text-[13px] tracking-wide text-chrome-dim transition-colors hover:text-platinum"
              >
                {divisionsLabel}
                <ChevronDown className="h-3.5 w-3.5" />
              </button>
              {divOpen && (
                <div className="absolute end-0 top-full min-w-[240px] pt-3">
                  <div className="overflow-hidden rounded-xl border border-hairline bg-void/95 p-1.5 shadow-2xl shadow-black/40 backdrop-blur-md">
                    {DIVISIONS.map((d) => (
                      <Link
                        key={d.key}
                        href={`/${locale}${d.href}`}
                        onClick={() => setDivOpen(false)}
                        className="flex items-center gap-3 rounded-lg px-3 py-2.5 transition-colors hover:bg-graphite"
                      >
                        <span className="h-2.5 w-2.5 flex-none rounded-full" style={{ background: d.color }} aria-hidden />
                        <span className="flex flex-col">
                          <span className="text-[13px] font-semibold text-platinum">{divisionName(d, locale)}</span>
                          <span className="font-mono text-[10.5px] text-slate">
                            {locale === "ar" ? d.label.ar : d.label.en}
                          </span>
                        </span>
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="whitespace-nowrap font-mono text-[13px] tracking-wide text-chrome-dim transition-colors hover:text-platinum"
              >
                {link.label}
              </Link>
            ))}
          </nav>
          <div className="flex items-center gap-3">
            <Link
              href={`/${locale}/quote`}
              className="hidden rounded-md bg-ion px-4 py-2 font-mono text-[12px] font-semibold text-void transition-opacity hover:opacity-90 sm:block"
            >
              {dict.nav.quote}
            </Link>
            <Link
              href={otherHref}
              className="font-mono text-[12px] tracking-wide text-slate transition-colors hover:text-platinum"
            >
              {otherLocale === "ar" ? "العربية" : "EN"}
            </Link>
          </div>
        </div>
      </header>

      <div className="fixed inset-x-0 bottom-4 z-40 flex justify-center px-4 sm:hidden">
        <LimelightNav
          items={mobileNavItems}
          activeIndex={mobileActiveIndex === -1 ? 0 : mobileActiveIndex}
          className="shadow-2xl shadow-black/40"
        />
      </div>
    </>
  );
}
