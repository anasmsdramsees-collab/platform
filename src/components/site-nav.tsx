"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Locale } from "@/lib/i18n/config";
import type { Dictionary } from "@/lib/i18n/dictionary";
import Logo from "./logo";

export default function SiteNav({ locale, dict }: { locale: Locale; dict: Dictionary }) {
  const pathname = usePathname() || `/${locale}`;
  const rest = pathname.replace(/^\/(en|ar)/, "") || "";
  const otherLocale: Locale = locale === "en" ? "ar" : "en";
  const otherHref = `/${otherLocale}${rest}`;

  const links = [
    { href: `/${locale}/products`, label: dict.nav.products },
    { href: `/${locale}/apps`, label: dict.nav.apps },
    { href: `/${locale}/about`, label: dict.nav.about },
    { href: `/${locale}/contact`, label: dict.nav.contact },
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-hairline bg-void/85 backdrop-blur-sm">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-5 py-4 sm:px-8">
        <Logo locale={locale} />
        <nav className="hidden items-center gap-8 sm:flex">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="font-mono text-[13px] tracking-wide text-chrome-dim transition-colors hover:text-platinum"
            >
              {link.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-4">
          <Link
            href={otherHref}
            className="font-mono text-[12px] tracking-wide text-slate transition-colors hover:text-platinum"
          >
            {otherLocale === "ar" ? "العربية" : "EN"}
          </Link>
        </div>
      </div>
      <nav className="flex items-center gap-6 overflow-x-auto border-t border-hairline px-5 py-2.5 sm:hidden">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="whitespace-nowrap font-mono text-[13px] tracking-wide text-chrome-dim hover:text-platinum"
          >
            {link.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
