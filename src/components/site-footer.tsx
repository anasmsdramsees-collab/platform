import Link from "next/link";
import type { Locale } from "@/lib/i18n/config";
import type { Dictionary } from "@/lib/i18n/dictionary";
import Logo from "./logo";

export default function SiteFooter({ locale, dict }: { locale: Locale; dict: Dictionary }) {
  const year = new Date().getFullYear();
  return (
    <footer className="border-t border-hairline">
      <div className="mx-auto flex max-w-6xl flex-col gap-10 px-5 py-14 sm:px-8 md:flex-row md:items-start md:justify-between">
        <div className="max-w-xs">
          <Logo locale={locale} />
          <p className="mt-4 font-mono text-[12.5px] text-slate">{dict.footer.tagline}</p>
        </div>
        <div className="grid grid-cols-2 gap-10 sm:grid-cols-4">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-widest text-slate">
              {dict.footer.products}
            </p>
            <Link
              href={`/${locale}/products`}
              className="mt-3 block text-sm text-chrome-dim transition-colors hover:text-platinum"
            >
              {dict.nav.products}
            </Link>
            <Link
              href={`/${locale}/store`}
              className="mt-2 block text-sm text-chrome-dim transition-colors hover:text-platinum"
            >
              {dict.nav.store}
            </Link>
            <Link
              href={`/${locale}/solutions`}
              className="mt-2 block text-sm text-chrome-dim transition-colors hover:text-platinum"
            >
              {dict.nav.solutions}
            </Link>
            <Link
              href={`/${locale}/services`}
              className="mt-2 block text-sm text-chrome-dim transition-colors hover:text-platinum"
            >
              {dict.nav.services}
            </Link>
          </div>
          <div>
            <p className="font-mono text-[11px] uppercase tracking-widest text-slate">
              {dict.footer.apps}
            </p>
            <Link
              href={`/${locale}/apps`}
              className="mt-3 block text-sm text-chrome-dim transition-colors hover:text-platinum"
            >
              Syltra TV
            </Link>
            <Link
              href={`/${locale}/apps`}
              className="mt-2 block text-sm text-chrome-dim transition-colors hover:text-platinum"
            >
              {locale === "ar" ? "سيلترا هوم" : "Syltra Home"}
            </Link>
          </div>
          <div>
            <p className="font-mono text-[11px] uppercase tracking-widest text-slate">
              {dict.footer.company}
            </p>
            <Link
              href={`/${locale}/about`}
              className="mt-3 block text-sm text-chrome-dim transition-colors hover:text-platinum"
            >
              {dict.nav.about}
            </Link>
            <Link
              href={`/${locale}/faq`}
              className="mt-2 block text-sm text-chrome-dim transition-colors hover:text-platinum"
            >
              {dict.nav.faq}
            </Link>
          </div>
          <div>
            <p className="font-mono text-[11px] uppercase tracking-widest text-slate">
              {dict.footer.contact}
            </p>
            <Link
              href={`/${locale}/contact`}
              className="mt-3 block text-sm text-chrome-dim transition-colors hover:text-platinum"
            >
              {dict.nav.contact}
            </Link>
            <Link
              href={`/${locale}/quote`}
              className="mt-2 block text-sm text-chrome-dim transition-colors hover:text-platinum"
            >
              {dict.nav.quote}
            </Link>
            <a
              href="https://www.instagram.com/syltrahome/"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 block text-sm text-chrome-dim transition-colors hover:text-platinum"
            >
              Instagram
            </a>
            <a
              href="https://www.tiktok.com/@syltra.home"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 block text-sm text-chrome-dim transition-colors hover:text-platinum"
            >
              TikTok
            </a>
            <a
              href={`https://wa.me/966533826009`}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 block text-sm text-chrome-dim transition-colors hover:text-platinum"
            >
              WhatsApp
            </a>
          </div>
        </div>
      </div>
      <div className="mx-auto max-w-6xl px-5 pb-10 sm:px-8">
        <p className="font-mono text-[11px] text-slate">
          © {year} Syltra One®. {dict.footer.rights}
        </p>
      </div>
    </footer>
  );
}
