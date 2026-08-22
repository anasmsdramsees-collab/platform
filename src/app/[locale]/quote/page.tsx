import type { Metadata } from "next";
import { locales, isLocale, type Locale } from "@/lib/i18n/config";
import { pageMetadata } from "@/lib/seo";
import { QuoteForm } from "@/components/ui/quote-form";
import { InfoCard } from "@/components/ui/info-card";
import { quoteCopy } from "@/lib/quote-copy";

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const c = quoteCopy[locale];
  return pageMetadata({ locale, path: "/quote", title: `${c.title} | Syltra One`, description: c.subtitle });
}

export default async function QuotePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const c = quoteCopy[locale];

  return (
    <section>
      <div className="mx-auto max-w-3xl px-5 py-20 sm:px-8 sm:py-24">
        <div className="text-center">
          <p className="font-mono text-[12px] uppercase tracking-[0.14em] text-slate">{c.eyebrow}</p>
          <h1 className="font-display mt-3 text-balance text-4xl font-bold text-platinum sm:text-5xl">
            {c.title}
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-chrome-dim">{c.subtitle}</p>
        </div>

        <div className="mt-10 grid gap-4 sm:grid-cols-3">
          {c.promises.map((p) => (
            <InfoCard key={p.name} className="p-5">
              <p className="text-sm font-semibold leading-snug text-platinum">{p.name}</p>
              <p className="mt-2 text-[13px] leading-relaxed text-chrome-dim">{p.desc}</p>
            </InfoCard>
          ))}
        </div>

        <div className="mt-8">
          <QuoteForm copy={c} source="quote-page" />
        </div>
      </div>
    </section>
  );
}
