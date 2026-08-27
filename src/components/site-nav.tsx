"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Package,
  LayoutGrid,
  Info,
  Mail,
  ShoppingBag,
  Layers,
  Wrench,
  Boxes,
  Home,
  Settings,
  Route,
  ChevronDown,
} from "lucide-react";
import type { Locale } from "@/lib/i18n/config";
import type { Dictionary } from "@/lib/i18n/dictionary";
import { DIVISIONS, divisionName, type DivisionMeta } from "@/lib/divisions";
import Logo from "./logo";
import { LimelightNav, type NavItem } from "./limelight-nav";

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

  const t = {
    divisions: locale === "ar" ? "الأقسام" : "Divisions",
    services: locale === "ar" ? "الخدمات" : "Services",
    solutions: locale === "ar" ? "الحلول" : "Solutions",
    flow: locale === "ar" ? "مسار العمل" : "Process",
    life: locale === "ar" ? "لايف" : "Life",
  };

  // Which context are we in?
  const activeDivision: DivisionMeta | undefined = DIVISIONS.find(
    (d) => d.key === seg && d.key !== "life"
  );
  const mode: "life" | "division" | "umbrella" = activeDivision
    ? "division"
    : LIFE_SEGMENTS.has(seg)
      ? "life"
      : "umbrella";

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
  );

  // Desktop links per context (Store appears in Life only).
  let desktopLinks: { href: string; label: string }[] = [];
  if (mode === "life") {
    desktopLinks = [
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
    desktopLinks = [
      { href: `${base}#services`, label: t.services },
      { href: `${base}#solutions`, label: t.solutions },
      { href: `${base}#flow`, label: t.flow },
      { href: `/${locale}/contact`, label: dict.nav.contact },
    ];
  } else {
    desktopLinks = [
      { href: `/${locale}/about`, label: dict.nav.about },
      { href: `/${locale}/contact`, label: dict.nav.contact },
    ];
  }

  // Mobile items per context.
  let mobileNavItems: NavItem[];
  if (mode === "life") {
    mobileNavItems = [
      { id: "products", icon: <Package />, label: dict.nav.products, href: `/${locale}/products` },
      { id: "store", icon: <ShoppingBag />, label: dict.nav.store, href: `/${locale}/store` },
      { id: "builder", icon: <Boxes />, label: dict.nav.builder, href: `/${locale}/builder` },
      { id: "solutions", icon: <Layers />, label: dict.nav.solutions, href: `/${locale}/solutions` },
      { id: "services", icon: <Wrench />, label: dict.nav.services, href: `/${locale}/services` },
      { id: "apps", icon: <LayoutGrid />, label: dict.nav.apps, href: `/${locale}/apps` },
      { id: "about", icon: <Info />, label: dict.nav.about, href: `/${locale}/about` },
      { id: "contact", icon: <Mail />, label: dict.nav.contact, href: `/${locale}/contact` },
    ];
  } else if (mode === "division" && activeDivision) {
    const base = `/${locale}${activeDivision.href}`;
    mobileNavItems = [
      { id: "divisions", icon: <LayoutGrid />, label: t.divisions, href: `/${locale}#divisions` },
      { id: "services", icon: <Wrench />, label: t.services, href: `${base}#services` },
      { id: "solutions", icon: <Settings />, label: t.solutions, href: `${base}#solutions` },
      { id: "flow", icon: <Route />, label: t.flow, href: `${base}#flow` },
      { id: "contact", icon: <Mail />, label: dict.nav.contact, href: `/${locale}/contact` },
    ];
  } else {
    mobileNavItems = [
      { id: "divisions", icon: <LayoutGrid />, label: t.divisions, href: `/${locale}#divisions` },
      { id: "life", icon: <Home />, label: t.life, href: `/${locale}/life` },
      { id: "about", icon: <Info />, label: dict.nav.about, href: `/${locale}/about` },
      { id: "contact", icon: <Mail />, label: dict.nav.contact, href: `/${locale}/contact` },
    ];
  }
  const mobileActiveIndex = mobileNavItems.findIndex((item) =>
    pathname.startsWith(item.href!.split("#")[0])
  );

  return (
    <>
      <header className="sticky top-0 z-40 border-b border-hairline bg-void/85 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-5 py-4 sm:px-8">
          <Logo locale={locale} />
          <nav className="hidden items-center gap-5 lg:flex lg:gap-7">
            {mode !== "life" && DivisionsDropdown}
            {desktopLinks.map((link) => (
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
