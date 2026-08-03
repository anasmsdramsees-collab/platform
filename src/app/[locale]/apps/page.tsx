import Link from "next/link";
import type { Metadata } from "next";
import { isLocale, type Locale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n/get-dictionary";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const dict = getDictionary(locale);
  return { title: dict.meta.titleApps, description: dict.meta.description };
}

export default async function AppsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const dict = getDictionary(locale);
  const a = dict.appsPage;

  return (
    <section>
      <div className="mx-auto max-w-4xl px-5 py-20 text-center sm:px-8">
        <p className="font-mono text-[12px] tracking-[0.14em] text-slate uppercase">
          {a.eyebrow}
        </p>
        <h1 className="font-display mt-3 text-balance text-4xl font-bold text-platinum sm:text-5xl">
          {a.title}
        </h1>
        <p className="mx-auto mt-5 max-w-xl text-chrome-dim">{a.subtitle}</p>
      </div>

      <div className="mx-auto max-w-6xl px-5 pb-24 sm:px-8">
        <div className="grid grid-cols-1 gap-px overflow-hidden bg-hairline sm:grid-cols-2">
          {a.cards.map((card) => (
            <Link
              key={card.slug}
              href={`/${locale}/apps/${card.slug}`}
              className="group bg-void p-8 transition-colors hover:bg-graphite sm:p-10"
            >
              <p className="font-mono text-[11px] uppercase tracking-widest text-slate">
                {card.status}
              </p>
              <p className="font-display mt-4 text-2xl font-bold text-platinum">{card.name}</p>
              <p className="mt-3 text-chrome-dim">{card.tagline}</p>
              <p className="mt-3 text-sm text-chrome-dim">{card.desc}</p>
              <p className="mt-6 font-mono text-sm text-ion transition-opacity group-hover:opacity-80">
                {locale === "ar" ? "التفاصيل" : "Learn more"} →
              </p>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
