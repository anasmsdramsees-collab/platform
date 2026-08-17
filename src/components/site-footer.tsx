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
          </div>
        </div>
      </div>
      <div className="mx-auto max-w-6xl px-5 pb-10 sm:px-8">
        <p className="font-mono text-[11px] text-slate">
          © {year} Syltra SMART®. {dict.footer.rights}
        </p>
      </div>
    </footer>
  );
}
