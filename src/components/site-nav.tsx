"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Package, LayoutGrid, Info, Mail, ShoppingBag, Layers, Wrench, Boxes } from "lucide-react";
import type { Locale } from "@/lib/i18n/config";
import type { Dictionary } from "@/lib/i18n/dictionary";
import Logo from "./logo";
import { LimelightNav, type NavItem } from "./limelight-nav";

export default function SiteNav({ locale, dict }: { locale: Locale; dict: Dictionary }) {
  const pathname = usePathname() || `/${locale}`;
  const rest = pathname.replace(/^\/(en|ar)/, "") || "";
  const otherLocale: Locale = locale === "en" ? "ar" : "en";
  const otherHref = `/${otherLocale}${rest}`;

  const divisionsLabel = locale === "ar" ? "الأقسام" : "Divisions";

  const links = [
    { href: `/${locale}#divisions`, label: divisionsLabel },
    { href: `/${locale}/products`, label: dict.nav.products },
    { href: `/${locale}/store`, label: dict.nav.store },
    { href: `/${locale}/builder`, label: dict.nav.builder },
    { href: `/${locale}/solutions`, label: dict.nav.solutions },
    { href: `/${locale}/services`, label: dict.nav.services },
    { href: `/${locale}/apps`, label: dict.nav.apps },
    { href: `/${locale}/about`, label: dict.nav.about },
    { href: `/${locale}/contact`, label: dict.nav.contact },
  ];

  const mobileNavItems: NavItem[] = [
    { id: "products", icon: <Package />, label: dict.nav.products, href: `/${locale}/products` },
    { id: "store", icon: <ShoppingBag />, label: dict.nav.store, href: `/${locale}/store` },
    { id: "builder", icon: <Boxes />, label: dict.nav.builder, href: `/${locale}/builder` },
    { id: "solutions", icon: <Layers />, label: dict.nav.solutions, href: `/${locale}/solutions` },
    { id: "services", icon: <Wrench />, label: dict.nav.services, href: `/${locale}/services` },
    { id: "apps", icon: <LayoutGrid />, label: dict.nav.apps, href: `/${locale}/apps` },
    { id: "about", icon: <Info />, label: dict.nav.about, href: `/${locale}/about` },
    { id: "contact", icon: <Mail />, label: dict.nav.contact, href: `/${locale}/contact` },
  ];
  const mobileActiveIndex = mobileNavItems.findIndex((item) => pathname.startsWith(item.href!));

  return (
    <>
      <header className="sticky top-0 z-40 border-b border-hairline bg-void/85 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-5 py-4 sm:px-8">
          <Logo locale={locale} />
          <nav className="hidden items-center gap-5 lg:flex lg:gap-7">
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
