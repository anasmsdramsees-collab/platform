"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Locale } from "@/lib/i18n/config";
import { HEALTH, HEALTH_NAV } from "@/lib/health-content";
import HealthLogo from "./health-logo";

export default function HealthNav({ locale }: { locale: Locale }) {
  const pathname = usePathname() || `/${locale}/health`;
  const [open, setOpen] = useState(false);

  // The admin area renders its own chrome.
  if (pathname.includes("/health/admin")) return null;

  const ar = locale === "ar";
  const base = `/${locale}/health`;
  const other: Locale = locale === "ar" ? "en" : "ar";

  // Primary links kept short on the bar; the rest live in the mobile sheet.
  const primary = HEALTH_NAV.filter((n) =>
    ["", "/how-it-works", "/app", "/accessibility", "/integrations", "/privacy"].includes(n.href)
  );

  const isActive = (href: string) => {
    const full = href === "" ? base : `${base}${href}`;
    return href === "" ? pathname === base : pathname.startsWith(full);
  };

  return (
    <header className="sticky top-0 z-50 border-b border-hairline bg-void/85 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-4 sm:px-8">
        <HealthLogo locale={locale} />

        <nav className="hidden items-center gap-8 lg:flex">
          {primary.map((n) => (
            <Link
              key={n.href}
              href={n.href === "" ? base : `${base}${n.href}`}
              className="relative py-1 text-sm text-chrome transition-colors hover:text-platinum"
            >
              {ar ? n.label.ar : n.label.en}
              {isActive(n.href) && (
                <span className="absolute inset-x-0 -bottom-0.5 h-px" style={{ backgroundColor: HEALTH.accent }} />
              )}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <Link
            href={`/${other}/health${pathname.replace(/^\/(en|ar)\/health/, "") || ""}`}
            className="hidden font-mono text-[12px] uppercase tracking-widest text-slate transition-colors hover:text-platinum sm:inline"
          >
            {locale === "ar" ? "EN" : "ع"}
          </Link>
          <Link
            href={`${base}/contact`}
            className="hidden rounded-full border px-5 py-2 text-sm font-semibold transition-colors sm:inline-flex"
            style={{ borderColor: HEALTH.accent, color: HEALTH.accent }}
          >
            {ar ? "انضم" : "Explore"}
          </Link>
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            className="inline-flex h-9 w-9 items-center justify-center text-platinum lg:hidden"
            aria-label={ar ? "القائمة" : "Menu"}
            aria-expanded={open}
          >
            <span className="relative block h-4 w-5">
              <span className={`absolute inset-x-0 top-0 h-0.5 bg-current transition-transform ${open ? "translate-y-[7px] rotate-45" : ""}`} />
              <span className={`absolute inset-x-0 top-1/2 h-0.5 -translate-y-1/2 bg-current transition-opacity ${open ? "opacity-0" : ""}`} />
              <span className={`absolute inset-x-0 bottom-0 h-0.5 bg-current transition-transform ${open ? "-translate-y-[7px] -rotate-45" : ""}`} />
            </span>
          </button>
        </div>
      </div>

      {open && (
        <div className="border-t border-hairline lg:hidden">
          <nav className="mx-auto grid max-w-6xl gap-1 px-5 py-4 sm:px-8">
            {HEALTH_NAV.map((n) => (
              <Link
                key={n.href}
                href={n.href === "" ? base : `${base}${n.href}`}
                onClick={() => setOpen(false)}
                className="border-b border-hairline py-3 text-[15px] text-chrome transition-colors hover:text-platinum"
              >
                {ar ? n.label.ar : n.label.en}
              </Link>
            ))}
            <Link
              href={`/${other}/health${pathname.replace(/^\/(en|ar)\/health/, "") || ""}`}
              onClick={() => setOpen(false)}
              className="flex items-center justify-between border-b border-hairline py-3 text-[15px] text-chrome transition-colors hover:text-platinum"
            >
              <span>{ar ? "اللغة" : "Language"}</span>
              <span className="font-mono text-[13px] uppercase tracking-widest" style={{ color: HEALTH.accent }}>
                {locale === "ar" ? "English" : "العربية"}
              </span>
            </Link>
            <Link
              href={`${base}/contact`}
              onClick={() => setOpen(false)}
              className="mt-3 inline-flex items-center justify-center rounded-full px-5 py-3 text-sm font-semibold text-void"
              style={{ backgroundColor: HEALTH.accent }}
            >
              {ar ? "انضم للتجربة المبكرة" : "Join Early Access"}
            </Link>
          </nav>
        </div>
      )}
    </header>
  );
}
