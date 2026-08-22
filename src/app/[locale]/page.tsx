import Link from "next/link";
import Image from "next/image";
import type { Metadata } from "next";
import { isLocale, type Locale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n/get-dictionary";
import { productCatalog } from "@/lib/products";
import HeroLightsPanel from "@/components/hero-lights-panel";
import CurtainsOverlay from "@/components/curtains-overlay";
import ProtocolOrbit from "@/components/protocol-orbit";
import ParticlesBg from "@/components/ui/particles-bg";
import { HeroCarousel } from "@/components/ui/hero-carousel";
import { ImageSlider } from "@/components/ui/image-slider";
import { Testimonials } from "@/components/ui/testimonials";
import { InfoCard } from "@/components/ui/info-card";
import { HoverBorderGradientLink } from "@/components/hover-border-gradient";
import { assetPath } from "@/lib/base-path";
import { pageMetadata } from "@/lib/seo";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const dict = getDictionary(locale);
  return pageMetadata({ locale, path: "", title: dict.meta.titleHome, description: dict.meta.description });
}

export default async function HomePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const dict = getDictionary(locale);

  const heroSlides =
    locale === "ar"
      ? [
          {
            src: "/hero/home-dashboard.jpg",
            label: "سيلترا هوم",
            title: "كل غرفة. شاشة واحدة.",
            caption: "خريطة حية لبيتك، ومشاهد جاهزة تعمل بلمسة واحدة.",
          },
          {
            src: "/hero/home-arrive.jpg",
            label: "سيلترا هوم",
            title: "يستقبلك البيت جاهزًا.",
            caption: "الإضاءة مضاءة والتكييف مضبوط قبل أن تفتح الباب.",
          },
          {
            src: "/hero/tv-interface.jpg",
            label: "سيلترا تي في",
            title: "شاشة تدير البيت كله.",
            caption: "قنواتك وأفلامك، والإضاءة والمناخ في متناول يدك.",
          },
          {
            src: "/hero/tv-family.jpg",
            label: "سيلترا تي في",
            title: "ليلة فيلم بمشهد واحد.",
            caption: "تخفت الإضاءة، وتُغلق الستائر، ويبدأ العرض.",
          },
          {
            src: "/hero/home-remote.jpg",
            label: "سيلترا هوم",
            title: "بيتك معك أينما كنت.",
            caption: "اطمئن عليه وتحكم فيه من أي مدينة في العالم.",
          },
        ]
      : [
          {
            src: "/hero/home-dashboard.jpg",
            label: "Syltra Home",
            title: "Every room. One screen.",
            caption: "A live map of your home, with scenes that run at a tap.",
          },
          {
            src: "/hero/home-arrive.jpg",
            label: "Syltra Home",
            title: "The house is ready before you are.",
            caption: "Lights on and the air cooled before you reach the door.",
          },
          {
            src: "/hero/tv-interface.jpg",
            label: "Syltra TV",
            title: "The screen that runs the house.",
            caption: "Your channels and films, with lights and climate in reach.",
          },
          {
            src: "/hero/tv-family.jpg",
            label: "Syltra TV",
            title: "Movie night in one scene.",
            caption: "Lights dim, curtains close, and the film begins.",
          },
          {
            src: "/hero/home-remote.jpg",
            label: "Syltra Home",
            title: "Home travels with you.",
            caption: "Check in and take control from any city in the world.",
          },
        ];

  return (
    <>
      <CurtainsOverlay dict={dict.lightsPanel} />
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-hairline">
        <ParticlesBg
          className="pointer-events-none z-10"
          style={{
            maskImage:
              "linear-gradient(to bottom, #000 0%, #000 58%, rgba(0,0,0,0.55) 70%, rgba(0,0,0,0) 84%)",
            WebkitMaskImage:
              "linear-gradient(to bottom, #000 0%, #000 58%, rgba(0,0,0,0.55) 70%, rgba(0,0,0,0) 84%)",
          }}
        />
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "radial-gradient(65% 55% at 50% 0%, rgba(11,12,14,0.18), rgba(11,12,14,0.62) 75%)",
          }}
        />
        <div className="relative z-20 mx-auto max-w-4xl px-5 py-24 text-center sm:px-8 sm:py-32">
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
            <HoverBorderGradientLink
              href={`/${locale}/products`}
              className="bg-platinum text-void"
              containerClassName="gap-0"
            >
              {dict.hero.ctaProducts}
            </HoverBorderGradientLink>
            <HoverBorderGradientLink
              href={`/${locale}/about`}
              className="bg-void text-platinum"
              containerClassName="gap-0"
            >
              {dict.hero.ctaAbout}
            </HoverBorderGradientLink>
          </div>

          <div className="relative z-[35] mt-10">
            <HeroLightsPanel dict={dict.lightsPanel} locale={locale} />
          </div>
        </div>

        {/* Hero carousel */}
        <div className="relative z-0 mt-4 w-full sm:mt-10">
          <HeroCarousel slides={heroSlides} rtl={locale === "ar"} />
        </div>
      </section>

      {/* Stats */}
      <section className="border-b border-hairline">
        <div className="mx-auto grid max-w-6xl grid-cols-2 gap-4 px-5 py-12 sm:grid-cols-4 sm:px-8">
          {dict.stats.map((stat) => (
            <InfoCard key={stat.label} className="px-5 py-8 text-center">
              <p className="font-mono text-2xl font-medium text-ion sm:text-3xl">{stat.value}</p>
              <p className="mt-2 text-xs text-chrome-dim sm:text-sm">{stat.label}</p>
            </InfoCard>
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
          <div className="mt-14 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {dict.ecosystem.pillars.map((pillar, i) => (
              <InfoCard key={pillar.name}>
                <p className="font-mono text-xs text-ion">{String(i + 1).padStart(2, "0")}</p>
                <p className="mt-3 font-semibold leading-snug text-platinum">{pillar.name}</p>
                <p className="mt-2.5 text-sm leading-relaxed text-chrome-dim">{pillar.desc}</p>
              </InfoCard>
            ))}
          </div>
        </div>
      </section>

      {/* Why Syltra */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-4xl px-5 py-20 sm:px-8">
          <p className="text-center font-mono text-[12px] tracking-[0.14em] text-slate uppercase">
            {dict.why.eyebrow}
          </p>
          <h2 className="font-display mt-3 text-balance text-center text-3xl font-bold text-platinum sm:text-4xl">
            {dict.why.title}
          </h2>
          <div className="mt-12 grid gap-4 sm:grid-cols-2">
            {dict.why.items.map((item, i) => (
              <InfoCard key={item.name}>
                <span className="font-mono text-xs text-ion">{String(i + 1).padStart(2, "0")}</span>
                <p className="mt-3 font-semibold leading-snug text-platinum">{item.name}</p>
                <p className="mt-2.5 text-sm leading-relaxed text-chrome-dim">{item.desc}</p>
              </InfoCard>
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
          <ProtocolOrbit items={dict.protocols.items} coreLabel={locale === "ar" ? "محرك سيلترا التكيفي" : "SYLTRA ADAPTIVE"} />
          <div className="mt-12 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {dict.protocols.items.map((p) => (
              <InfoCard key={p.name}>
                <p className="font-mono text-sm font-semibold text-platinum">{p.name}</p>
                <p className="mt-2.5 text-sm leading-relaxed text-chrome-dim">{p.desc}</p>
              </InfoCard>
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
              <div
                key={card.slug}
                className="overflow-hidden rounded-2xl border border-hairline bg-graphite/70 transition-colors duration-300 hover:border-hairline-strong"
              >
                <div className="relative aspect-video overflow-hidden border-b border-hairline">
                  <ImageSlider
                    images={
                      card.slug === "home-assistant"
                        ? ["/hero/home-dashboard.jpg", "/hero/home-arrive.jpg", "/hero/home-remote.jpg"]
                        : ["/hero/tv-interface.jpg", "/hero/tv-family.jpg"]
                    }
                    alt={card.name}
                    offset={card.slug === "home-assistant" ? 0 : 2200}
                  />
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
              </div>
            ))}
          </div>
        </div>
      </section>

      <Testimonials
        eyebrow={dict.testimonials.eyebrow}
        title={dict.testimonials.title}
        subtitle={dict.testimonials.subtitle}
        testimonials={dict.testimonials.items}
      />

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
