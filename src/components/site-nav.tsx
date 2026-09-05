"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronDown, Menu, X } from "lucide-react";
import type { Locale } from "@/lib/i18n/config";
import type { Dictionary } from "@/lib/i18n/dictionary";
import { DIVISIONS, VISIBLE_DIVISIONS, divisionName, type DivisionMeta } from "@/lib/divisions";
import Logo from "./logo";

// Path segments that belong to the Life division (its own product world).
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

export default function SiteNav({ locale, dict }: { locale: Locale; dict: Dictionary }) {
  const pathname = usePathname() || `/${locale}`;
  const rest = pathname.replace(/^\/(en|ar)/, "") || "";
  const seg = rest.split("/").filter(Boolean)[0] || "";
  const otherLocale: Locale = locale === "en" ? "ar" : "en";
  const otherHref = `/${otherLocale}${rest}`;
  const [divOpen, setDivOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  // The HEALTH section ships its own green-accented chrome (see health/layout).
  if (seg === "health") return null;

  const t = {
    divisions: locale === "ar" ? "الأقسام" : "Divisions",
    services: locale === "ar" ? "الخدمات" : "Services",
    solutions: locale === "ar" ? "الحلول" : "Solutions",
    flow: locale === "ar" ? "مسار العمل" : "Process",
  };

  const activeDivision: DivisionMeta | undefined = DIVISIONS.find(
    (d) => d.key === seg && d.key !== "life"
  );
  const mode: "life" | "division" | "umbrella" = activeDivision
    ? "division"
    : LIFE_SEGMENTS.has(seg)
      ? "life"
      : "umbrella";

  // Links for the current context (Store appears in Life only).
  let links: { href: string; label: string }[] = [];
  if (mode === "life") {
    links = [
      { href: `/${locale}/products`, label: dict.nav.products },
      { href: `/${locale}/store`, label: dict.nav.store },
      { href: `/${locale}/builder`, label: dict.nav.builder },
      { href: `/${locale}/solutions`, label: dict.nav.solutions },
      { href: `/${locale}/services`, label: dict.nav.services },
      { href: `/${locale}/apps`, label: dict.nav.apps },
      { href: `/${locale}/about`, label: dict.nav.about },
      { href: `/${locale}/contact`, label: dict.nav.contact },
    ];
  } else if (mode === "division" && activeDivision) {
    const base = `/${locale}${activeDivision.href}`;
    links = [
      { href: `/${locale}`, label: locale === "ar" ? "سيلترا وان" : "Syltra One" },
      { href: `${base}#services`, label: t.services },
      { href: `${base}#solutions`, label: t.solutions },
      { href: `${base}#flow`, label: t.flow },
      { href: `/${locale}/contact`, label: dict.nav.contact },
    ];
  } else {
    links = [
      { href: `/${locale}/about`, label: dict.nav.about },
      { href: `/${locale}/blog`, label: locale === "ar" ? "المدونة" : "Blog" },
      { href: `/${locale}/contact`, label: dict.nav.contact },
    ];
  }

  const DivisionsDropdown = (
    <div className="relative" onMouseEnter={() => setDivOpen(true)} onMouseLeave={() => setDivOpen(false)}>
      <button
        type="button"
        aria-haspopup="true"
        aria-expanded={divOpen}
        onClick={() => setDivOpen((v) => !v)}
        className="flex items-center gap-1.5 font-mono text-[13px] tracking-wide text-chrome-dim transition-colors hover:text-platinum"
      >
        {t.divisions}
        <ChevronDown className="h-3.5 w-3.5" />
      </button>
      {divOpen && (
        <div className="absolute end-0 top-full min-w-[240px] pt-3">
          <div className="overflow-hidden rounded-xl border border-hairline bg-void/95 p-1.5 shadow-2xl shadow-black/40 backdrop-blur-md">
            <Link
              href={`/${locale}`}
              onClick={() => setDivOpen(false)}
              className="mb-1 flex items-center gap-3 rounded-lg border-b border-hairline px-3 py-2.5 transition-colors hover:bg-graphite"
            >
              <span className="h-2.5 w-2.5 flex-none rounded-full" style={{ background: "#BFC6D0" }} aria-hidden />
              <span className="text-[13px] font-semibold text-platinum">
                {locale === "ar" ? "سيلترا وان — الرئيسية" : "Syltra One — Home"}
              </span>
            </Link>
            {VISIBLE_DIVISIONS.map((d) => (
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
  );

  return (
    <header className="sticky top-0 z-40 border-b border-hairline bg-void/85 backdrop-blur-sm">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-5 py-4 sm:px-8">
        <Logo locale={locale} />

        {/* Desktop nav */}
        <nav className="hidden items-center gap-5 lg:flex lg:gap-7">
          {mode !== "life" && DivisionsDropdown}
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
          {mode !== "umbrella" && (
            <Link
              href={`/${locale}/quote`}
              className={`hidden rounded-md px-4 py-2 font-mono text-[12px] font-semibold text-void transition-opacity hover:opacity-90 sm:block ${
                activeDivision ? "" : "bg-ion"
              }`}
              style={activeDivision ? { backgroundColor: activeDivision.color } : undefined}
            >
              {dict.nav.quote}
            </Link>
          )}
          <Link
            href={otherHref}
            className="font-mono text-[12px] tracking-wide text-slate transition-colors hover:text-platinum"
          >
            {otherLocale === "ar" ? "العربية" : "EN"}
          </Link>
          {/* Mobile menu toggle */}
          <button
            type="button"
            aria-label={menuOpen ? "Close menu" : "Open menu"}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((v) => !v)}
            className="text-chrome-dim transition-colors hover:text-platinum lg:hidden"
          >
            {menuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
      </div>

      {/* Mobile menu panel */}
      {menuOpen && (
        <div className="border-t border-hairline bg-void/95 backdrop-blur-md lg:hidden">
          <nav className="mx-auto max-w-6xl px-5 py-4 sm:px-8">
            {mode !== "life" && (
              <div className="mb-2 border-b border-hairline pb-3">
                <p className="mb-1 font-mono text-[11px] uppercase tracking-widest text-slate">{t.divisions}</p>
                {VISIBLE_DIVISIONS.map((d) => (
                  <Link
                    key={d.key}
                    href={`/${locale}${d.href}`}
                    onClick={() => setMenuOpen(false)}
                    className="flex items-center gap-3 rounded-lg px-1 py-2.5 transition-colors hover:bg-graphite"
                  >
                    <span className="h-2.5 w-2.5 flex-none rounded-full" style={{ background: d.color }} aria-hidden />
                    <span className="text-sm font-semibold text-platinum">{divisionName(d, locale)}</span>
                  </Link>
                ))}
              </div>
            )}
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMenuOpen(false)}
                className="block px-1 py-2.5 font-mono text-sm text-chrome-dim transition-colors hover:text-platinum"
              >
                {link.label}
              </Link>
            ))}
            {mode !== "umbrella" && (
              <Link
                href={`/${locale}/quote`}
                onClick={() => setMenuOpen(false)}
                className="mt-3 block rounded-md px-4 py-3 text-center font-mono text-[13px] font-semibold text-void"
                style={{ backgroundColor: activeDivision ? activeDivision.color : "var(--color-ion, #4c8dff)" }}
              >
                {dict.nav.quote}
              </Link>
            )}
          </nav>
        </div>
      )}
    </header>
  );
}
