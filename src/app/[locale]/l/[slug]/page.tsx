import type { Metadata } from "next";
import Link from "next/link";
import Image from "next/image";
import { notFound } from "next/navigation";
import { locales, isLocale, type Locale } from "@/lib/i18n/config";
import { pageMetadata } from "@/lib/seo";
import { siteUrl, siteName } from "@/lib/site-config";
import { landings, findLanding, landingCopy } from "@/lib/landing";
import { productCatalog } from "@/lib/products";
import { assetPath } from "@/lib/base-path";
import { InfoCard } from "@/components/ui/info-card";
import { FaqCards } from "@/components/ui/faq-cards";
import { QuoteForm } from "@/components/ui/quote-form";
import JsonLd from "@/components/json-ld";
import { quoteCopy } from "@/lib/quote-copy";

export function generateStaticParams() {
  return locales.flatMap((locale) => landings.map((l) => ({ locale, slug: l.slug })));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}): Promise<Metadata> {
  const { locale: raw, slug } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const landing = findLanding(slug);
  if (!landing) return {};
  const c = landingCopy(landing, locale);
  return pageMetadata({ locale, path: `/l/${slug}`, title: c.title, description: c.description });
}

export default async function LandingPage({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}) {
  const { locale: raw, slug } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const landing = findLanding(slug);
  if (!landing) notFound();
  const c = landingCopy(landing, locale);
  const ar = locale === "ar";

  const all = productCatalog.flatMap((cat) => cat.items);
  const picks = landing.products
    .map((s) => all.find((p) => p.slug === s))
    .filter((p): p is NonNullable<typeof p> => Boolean(p));

  return (
    <>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@graph": [
            {
              "@type": "Service",
              name: c.h1,
              description: c.description,
              provider: { "@id": `${siteUrl}/#organization` },
              areaServed: { "@type": "City", name: ar ? "الرياض" : "Riyadh" },
              url: `${siteUrl}/${locale}/l/${slug}`,
            },
            {
              "@type": "FAQPage",
              mainEntity: c.faq.map((f) => ({
                "@type": "Question",
                name: f.q,
                acceptedAnswer: { "@type": "Answer", text: f.a },
              })),
            },
          ],
        }}
      />

      {/* Hero */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-4xl px-5 py-20 text-center sm:px-8 sm:py-24">
          <p className="font-mono text-[12px] uppercase tracking-[0.14em] text-slate">{siteName}</p>
          <h1 className="font-display mt-3 text-balance text-4xl font-bold text-platinum sm:text-5xl">
            {c.h1}
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-pretty leading-relaxed text-chrome-dim">{c.intro}</p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link
              href={`/${locale}/quote`}
              className="rounded-md bg-platinum px-7 py-3 text-sm font-semibold text-void transition-opacity hover:opacity-90"
            >
              {ar ? "احجز معاينة مجانية" : "Book a free survey"}
            </Link>
            <a
              href={`https://wa.me/966550098550?text=${encodeURIComponent(
                ar ? `مرحبًا، أستفسر عن: ${c.h1}` : `Hello, I'd like to ask about: ${c.h1}`
              )}`}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-md border border-hairline-strong px-7 py-3 text-sm font-semibold text-platinum transition-colors hover:border-ion"
            >
              {ar ? "واتساب" : "WhatsApp"}
            </a>
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-6xl px-5 py-16 sm:px-8">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {c.benefits.map((b) => (
              <InfoCard key={b.name}>
                <p className="font-semibold leading-snug text-platinum">{b.name}</p>
                <p className="mt-2.5 text-sm leading-relaxed text-chrome-dim">{b.desc}</p>
              </InfoCard>
            ))}
          </div>
        </div>
      </section>

      {/* Related products */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-6xl px-5 py-16 sm:px-8">
          <h2 className="font-display text-center text-2xl font-bold text-platinum sm:text-3xl">
            {ar ? "الأجهزة المستخدمة" : "The devices involved"}
          </h2>
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {picks.map((p) => {
              const copy = ar ? p.ar : p.en;
              return (
                <Link key={p.slug} href={`/${locale}/products/${p.slug}`} className="group block">
                  <InfoCard className="h-full overflow-hidden p-0">
                    {p.images?.[0] && (
                      <div className="relative aspect-[4/3] overflow-hidden border-b border-hairline">
                        <Image
                          src={assetPath(p.images[0])}
                          alt={p.name}
                          fill
                          sizes="(min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw"
                          className="object-cover transition-transform duration-500 group-hover:scale-105"
                        />
                      </div>
                    )}
                    <div className="p-6">
                      <p className="font-mono text-sm font-semibold text-platinum">{p.name}</p>
                      <p className="mt-2 text-sm leading-relaxed text-chrome-dim">{copy.tagline}</p>
                    </div>
                  </InfoCard>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-4xl px-5 py-16 sm:px-8">
          <h2 className="font-display text-center text-2xl font-bold text-platinum sm:text-3xl">
            {ar ? "أسئلة يسألها العملاء" : "Questions customers ask"}
          </h2>
          <div className="mt-10">
            <FaqCards items={c.faq} />
          </div>
        </div>
      </section>

      {/* Conversion */}
      <section>
        <div className="mx-auto max-w-3xl px-5 py-16 sm:px-8">
          <h2 className="font-display text-center text-2xl font-bold text-platinum sm:text-3xl">
            {ar ? "احجز معاينتك المجانية" : "Book your free survey"}
          </h2>
          <div className="mt-8">
            <QuoteForm copy={quoteCopy[locale]} source={`landing:${slug}`} />
          </div>
        </div>
      </section>
    </>
  );
}
