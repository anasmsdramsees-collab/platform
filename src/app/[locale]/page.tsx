import Link from "next/link";
import Image from "next/image";
import type { Metadata } from "next";
import { isLocale, type Locale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n/get-dictionary";
import { productCatalog } from "@/lib/products";
import HeroLightsPanel from "@/components/hero-lights-panel";
import CurtainsOverlay from "@/components/curtains-overlay";
import SyntraTvMockup from "@/components/syntra-tv-mockup";
import { assetPath } from "@/lib/base-path";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const dict = getDictionary(locale);
  return { title: dict.meta.titleHome, description: dict.meta.description };
}

export default async function HomePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const dict = getDictionary(locale);

  return (
    <>
      <CurtainsOverlay dict={dict.lightsPanel} />
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-hairline">
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "radial-gradient(60% 50% at 50% 0%, rgba(76,141,255,0.10), transparent 70%)",
          }}
        />
        <div className="relative mx-auto max-w-4xl px-5 py-24 text-center sm:px-8 sm:py-32">
          <p className="font-mono text-[12px] tracking-[0.14em] text-slate uppercase">
            {dict.hero.eyebrow}
          </p>
          <h1 className="font-display mt-5 text-balance text-4xl font-bold leading-[1.1] text-platinum sm:text-6xl">
            {dict.hero.title}
          </h1>
          <p className="mx-auto mt-6 max-w-xl text-balance text-base text-chrome-dim sm:text-lg">
            {dict.hero.subtitle}
          </p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link
              href={`/${locale}/products`}
              className="rounded-md bg-platinum px-6 py-3 text-sm font-semibold text-void transition-opacity hover:opacity-90"
            >
              {dict.hero.ctaProducts}
            </Link>
            <Link
              href={`/${locale}/about`}
              className="rounded-md border border-hairline-strong px-6 py-3 text-sm font-semibold text-platinum transition-colors hover:bg-graphite"
            >
              {dict.hero.ctaAbout}
            </Link>
          </div>

          <div className="relative z-[35] mt-10">
            <HeroLightsPanel dict={dict.lightsPanel} locale={locale} />
          </div>
        </div>

        {/* Hero product visual */}
        <div className="relative mt-4 aspect-[1536/852] w-full sm:mt-10">
          <Image
            src={assetPath("/brand/hero-products.jpg")}
            alt="The SYNTRA SMART ecosystem — hub, panel, lock, switch, sensors, camera, doorbell and more"
            fill
            priority
            sizes="100vw"
            className="object-cover object-top"
          />
          <div
            className="pointer-events-none absolute inset-0"
            style={{
              background:
                "linear-gradient(180deg, var(--color-void) 0%, rgba(11,12,14,0) 12%, rgba(11,12,14,0) 78%, var(--color-void) 100%)",
            }}
          />
        </div>
      </section>

      {/* Stats */}
      <section className="border-b border-hairline">
        <div className="mx-auto grid max-w-6xl grid-cols-2 gap-px overflow-hidden border-hairline bg-hairline sm:grid-cols-4">
          {dict.stats.map((stat) => (
            <div key={stat.label} className="bg-void px-5 py-10 text-center sm:px-6">
              <p className="font-mono text-2xl font-medium text-ion sm:text-3xl">{stat.value}</p>
              <p className="mt-2 text-xs text-chrome-dim sm:text-sm">{stat.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Ecosystem */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-6xl px-5 py-20 sm:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <p className="font-mono text-[12px] tracking-[0.14em] text-slate uppercase">
              {dict.ecosystem.eyebrow}
            </p>
            <h2 className="font-display mt-3 text-3xl font-bold text-platinum sm:text-4xl">
              {dict.ecosystem.title}
            </h2>
            <p className="mt-4 text-chrome-dim">{dict.ecosystem.subtitle}</p>
          </div>
          <div className="mt-14 grid grid-cols-1 gap-px overflow-hidden bg-hairline sm:grid-cols-2 lg:grid-cols-4">
            {dict.ecosystem.pillars.map((pillar, i) => (
              <div key={pillar.name} className="bg-void p-6">
                <p className="font-mono text-xs text-ion">{String(i + 1).padStart(2, "0")}</p>
                <p className="mt-3 font-semibold text-platinum">{pillar.name}</p>
                <p className="mt-2 text-sm text-chrome-dim">{pillar.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why SYNTRA */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-4xl px-5 py-20 sm:px-8">
          <p className="text-center font-mono text-[12px] tracking-[0.14em] text-slate uppercase">
            {dict.why.eyebrow}
          </p>
          <h2 className="font-display mt-3 text-balance text-center text-3xl font-bold text-platinum sm:text-4xl">
            {dict.why.title}
          </h2>
          <div className="mt-12 divide-y divide-hairline border-y border-hairline">
            {dict.why.items.map((item, i) => (
              <div key={item.name} className="flex items-start gap-6 py-6">
                <span className="font-mono text-sm text-ion">{String(i + 1).padStart(2, "0")}</span>
                <div>
                  <p className="font-semibold text-platinum">{item.name}</p>
                  <p className="mt-1 text-sm text-chrome-dim">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Product categories */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-6xl px-5 py-20 sm:px-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="font-mono text-[12px] tracking-[0.14em] text-slate uppercase">
                {dict.categories.eyebrow}
              </p>
              <h2 className="font-display mt-3 text-3xl font-bold text-platinum sm:text-4xl">
                {dict.categories.title}
              </h2>
              <p className="mt-3 max-w-lg text-chrome-dim">{dict.categories.subtitle}</p>
            </div>
            <Link
              href={`/${locale}/products`}
              className="font-mono text-sm text-ion transition-opacity hover:opacity-80"
            >
              {dict.categories.cta} →
            </Link>
          </div>
          <div className="mt-12 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {productCatalog.map((category) => {
              const copy = locale === "ar" ? category.ar : category.en;
              return (
                <Link
                  key={category.key}
                  href={`/${locale}/products#${category.key}`}
                  className="group rounded-lg border border-hairline p-6 transition-colors hover:border-hairline-strong hover:bg-graphite"
                >
                  <p className="font-semibold text-platinum">{copy.name}</p>
                  <p className="mt-2 text-sm text-chrome-dim">{copy.desc}</p>
                  <p className="mt-4 font-mono text-xs text-slate">
                    {category.items.length} {locale === "ar" ? "منتجات" : "products"}
                  </p>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* Protocols */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-6xl px-5 py-20 sm:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <p className="font-mono text-[12px] tracking-[0.14em] text-slate uppercase">
              {dict.protocols.eyebrow}
            </p>
            <h2 className="font-display mt-3 text-3xl font-bold text-platinum sm:text-4xl">
              {dict.protocols.title}
            </h2>
            <p className="mt-4 text-chrome-dim">{dict.protocols.subtitle}</p>
          </div>
          <div className="mt-12 grid grid-cols-2 gap-px overflow-hidden bg-hairline sm:grid-cols-3">
            {dict.protocols.items.map((p) => (
              <div key={p.name} className="bg-void p-6">
                <p className="font-mono text-sm text-platinum">{p.name}</p>
                <p className="mt-2 text-sm text-chrome-dim">{p.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Apps teaser */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-6xl px-5 py-20 sm:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <p className="font-mono text-[12px] tracking-[0.14em] text-slate uppercase">
              {dict.appsPage.eyebrow}
            </p>
            <h2 className="font-display mt-3 text-3xl font-bold text-platinum sm:text-4xl">
              {dict.appsPage.title}
            </h2>
            <p className="mt-4 text-chrome-dim">{dict.appsPage.subtitle}</p>
          </div>
          <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-2">
            {dict.appsPage.cards.map((card) => (
              <Link
                key={card.slug}
                href={`/${locale}/apps/${card.slug}`}
                className="group block overflow-hidden border border-hairline bg-void transition-colors hover:border-hairline-strong"
              >
                <div className="relative aspect-video overflow-hidden border-b border-hairline">
                  {card.slug === "home-assistant" ? (
                    <Image
                      src={assetPath("/brand/app-home-dashboard.jpg")}
                      alt={card.name}
                      fill
                      sizes="(min-width: 640px) 50vw, 100vw"
                      className="object-cover object-top transition-transform duration-500 group-hover:scale-[1.03]"
                    />
                  ) : (
                    <SyntraTvMockup locale={locale} />
                  )}
                </div>
                <div className="p-6 sm:p-8">
                  <p className="font-mono text-[11px] uppercase tracking-widest text-slate">
                    {card.status}
                  </p>
                  <div className="mt-4 flex items-center gap-3">
                    <Image
                      src={assetPath(
                        card.slug === "home-assistant"
                          ? "/brand/app-icon-home.png"
                          : "/brand/app-icon-tv.png"
                      )}
                      alt=""
                      width={64}
                      height={64}
                      className="h-8 w-8 rounded-md"
                    />
                    <p className="font-display text-xl font-bold text-platinum">{card.name}</p>
                  </div>
                  <p className="mt-2 text-sm text-chrome-dim">{card.tagline}</p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section>
        <div className="mx-auto max-w-3xl px-5 py-24 text-center sm:px-8">
          <h2 className="font-display text-balance text-3xl font-bold text-platinum sm:text-4xl">
            {dict.homeCta.title}
          </h2>
          <p className="mt-4 text-chrome-dim">{dict.homeCta.subtitle}</p>
          <Link
            href={`/${locale}/contact`}
            className="mt-8 inline-block rounded-md bg-platinum px-7 py-3 text-sm font-semibold text-void transition-opacity hover:opacity-90"
          >
            {dict.homeCta.button}
          </Link>
        </div>
      </section>
    </>
  );
}
