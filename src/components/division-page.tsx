import Link from "next/link";
import Image from "next/image";
import type { Locale } from "@/lib/i18n/config";
import type { DivisionMeta } from "@/lib/divisions";
import { divisionName } from "@/lib/divisions";
import { DIVISION_CONTENT, pick } from "@/lib/division-content";
import { DIVISION_FAQ } from "@/lib/faq";
import ParticlesBg from "@/components/ui/particles-bg";
import { HeroCarousel } from "@/components/ui/hero-carousel";
import FaqSection from "@/components/faq-section";
import { assetPath } from "@/lib/base-path";

export default function DivisionPage({
  division,
  locale,
}: {
  division: DivisionMeta;
  locale: Locale;
}) {
  const c = DIVISION_CONTENT[division.key as keyof typeof DIVISION_CONTENT];
  const accent = division.color;
  const name = divisionName(division, locale);

  const heroSlides = c.heroSlides.map((s) => ({
    src: s.image ?? division.image,
    label: name,
    title: pick(s.title, locale),
    caption: pick(s.caption, locale),
  }));

  return (
    <>
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
          style={{ background: "radial-gradient(65% 55% at 50% 0%, rgba(11,12,14,0.15), rgba(11,12,14,0.6) 75%)" }}
        />
        <div
          className="pointer-events-none absolute inset-0 z-[11]"
          style={{
            background: `radial-gradient(70% 55% at 82% 8%, ${hexA(accent, 0.18)}, transparent 60%)`,
            mixBlendMode: "screen",
          }}
        />
        <div className="relative z-20 mx-auto max-w-4xl px-5 py-24 text-center sm:px-8 sm:py-32">
          <div dir="ltr" className="mx-auto mb-5 flex items-center justify-center gap-2">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={assetPath("/brand/divisions/word.png")} alt="SYLTRA" className="h-6 w-auto sm:h-7" />
            <span className="h-5 w-px" style={{ background: "var(--color-hairline, rgba(199,204,211,.2))" }} />
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={assetPath(division.logo)} alt={name} className="h-6 w-auto sm:h-7" />
          </div>
          <h1 className="font-display mt-4 text-balance text-4xl font-bold leading-[1.1] text-platinum sm:text-6xl">
            {pick(c.h1, locale)}
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-balance text-base text-chrome-dim sm:text-lg">
            {pick(c.intro, locale)}
          </p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link
              href={`/${locale}/contact`}
              className="rounded-md px-7 py-3 text-sm font-semibold text-void transition-opacity hover:opacity-90"
              style={{ background: accent }}
            >
              {pick(c.ctaTitle, locale)}
            </Link>
            <a
              href="tel:0550098550"
              className="rounded-md border border-hairline-strong px-7 py-3 font-mono text-sm font-semibold text-platinum transition-colors hover:border-ion"
            >
              0550098550
            </a>
          </div>
        </div>

        {/* Hero carousel, division facets */}
        <div className="relative z-0 mt-4 w-full sm:mt-8">
          <HeroCarousel slides={heroSlides} rtl={locale === "ar"} />
        </div>
      </section>

      {/* Services, matrix grid */}
      <section id="services" className="scroll-mt-20 border-b border-hairline">
        <div className="mx-auto max-w-6xl px-5 py-24 sm:px-8">
          <p className="font-mono text-[12px] tracking-[0.14em] text-slate uppercase">{pick(c.servicesEyebrow, locale)}</p>
          <h2 className="font-display mt-3 max-w-3xl text-balance text-3xl font-bold text-platinum sm:text-4xl">
            {pick(c.servicesTitle, locale)}
          </h2>
          <div className="mt-12 grid grid-cols-1 border-l border-t border-hairline sm:grid-cols-2 lg:grid-cols-3">
            {c.services.map((s, i) => (
              <div key={i} className="border-b border-r border-hairline p-7 transition-colors hover:bg-graphite/40">
                <span className="font-display text-xl font-bold tabular-nums" style={{ color: accent }}>
                  {String(i + 1).padStart(2, "0")}
                </span>
                <p className="mt-4 font-semibold leading-snug text-platinum">{pick(s.title, locale)}</p>
                <p className="mt-2 text-sm leading-relaxed text-chrome-dim">{pick(s.desc, locale)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Systems / solutions, gallery */}
      <section id="solutions" className="scroll-mt-20 border-b border-hairline">
        <div className="mx-auto max-w-6xl px-5 py-24 sm:px-8">
          <p className="font-mono text-[12px] tracking-[0.14em] text-slate uppercase">{pick(c.systemsEyebrow, locale)}</p>
          <h2 className="font-display mt-3 max-w-3xl text-balance text-3xl font-bold text-platinum sm:text-4xl">
            {pick(c.systemsTitle, locale)}
          </h2>
          <div className="mt-12 grid grid-cols-2 gap-x-5 gap-y-9 sm:grid-cols-3 lg:grid-cols-4">
            {c.systems.map((s, i) => (
              <figure key={i} className="group">
                {s.img ? (
                  <div className="relative aspect-[4/3] overflow-hidden">
                    <Image
                      src={assetPath(s.img)}
                      alt={pick(s.title, locale)}
                      fill
                      sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
                      className="object-cover transition-transform duration-[900ms] ease-out group-hover:scale-[1.03]"
                    />
                  </div>
                ) : (
                  <div className="flex aspect-[4/3] items-center justify-center border border-hairline">
                    <span className="px-3 text-center font-mono text-[11px] uppercase tracking-widest text-slate">
                      {s.en || pick(s.title, locale)}
                    </span>
                  </div>
                )}
                <figcaption className="mt-3.5">
                  <span
                    className="block h-px w-8 transition-[width] duration-500 group-hover:w-14"
                    style={{ background: accent }}
                    aria-hidden
                  />
                  <p className="mt-3 font-semibold leading-snug text-platinum">{pick(s.title, locale)}</p>
                  {s.en ? (
                    <p className="mt-0.5 font-mono text-[10.5px] uppercase tracking-widest text-slate">{s.en}</p>
                  ) : null}
                </figcaption>
              </figure>
            ))}
          </div>
          <p className="mt-6 max-w-3xl text-sm leading-relaxed text-chrome-dim">{pick(c.systemsNote, locale)}</p>
        </div>
      </section>

      {/* Statement band */}
      <section style={{ background: accent }}>
        <div className="mx-auto max-w-5xl px-5 py-20 sm:px-8">
          <h2 className="font-display text-balance text-3xl font-extrabold leading-tight sm:text-5xl" style={{ color: "#0b0c0e" }}>
            {pick(c.statementTitle, locale)}
          </h2>
          <p className="mt-5 max-w-2xl text-base sm:text-lg" style={{ color: "rgba(11,12,14,0.82)" }}>
            {pick(c.statementBody, locale)}
          </p>
        </div>
      </section>

      {/* Flow, editorial timeline */}
      <section id="flow" className="scroll-mt-20 border-b border-hairline">
        <div className="mx-auto max-w-6xl px-5 py-24 sm:px-8">
          <p className="font-mono text-[12px] tracking-[0.14em] text-slate uppercase">{pick(c.flowEyebrow, locale)}</p>
          <h2 className="font-display mt-3 max-w-3xl text-balance text-3xl font-bold text-platinum sm:text-4xl">
            {pick(c.flowTitle, locale)}
          </h2>
          <div className="mt-12 grid grid-cols-1 border-t border-hairline sm:grid-cols-2 lg:grid-cols-5">
            {c.flow.map((f, i) => (
              <div key={i} className="border-b border-hairline px-1 py-7 sm:border-l sm:first:border-l-0 sm:ps-6">
                <span className="font-mono text-xs" style={{ color: accent }}>{String(i + 1).padStart(2, "0")}</span>
                <p className="mt-3 font-semibold leading-snug text-platinum">{pick(f.title, locale)}</p>
                <p className="mt-1.5 text-sm leading-relaxed text-chrome-dim">{pick(f.desc, locale)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      {DIVISION_FAQ[division.key] ? (
        <FaqSection items={DIVISION_FAQ[division.key]} locale={locale} accent={accent} />
      ) : null}

      {/* CTA */}
      <section id="contact" className="scroll-mt-20">
        <div className="mx-auto max-w-3xl px-5 py-24 text-center sm:px-8">
          <h2 className="font-display text-balance text-3xl font-bold text-platinum sm:text-4xl">{pick(c.ctaTitle, locale)}</h2>
          <p className="mt-4 text-chrome-dim">{pick(c.ctaBody, locale)}</p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link
              href={`/${locale}/contact`}
              className="rounded-md px-7 py-3 text-sm font-semibold text-void transition-opacity hover:opacity-90"
              style={{ background: accent }}
            >
              {locale === "ar" ? "تواصل معنا" : "Contact us"}
            </Link>
            <Link
              href={`/${locale}`}
              className="rounded-md border border-hairline-strong px-7 py-3 text-sm font-semibold text-platinum transition-colors hover:border-ion"
            >
              {locale === "ar" ? "كل الأقسام" : "All divisions"}
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}

/** hex (#rrggbb) + alpha → rgba() string. */
function hexA(hex: string, a: number) {
  const h = hex.replace("#", "");
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${a})`;
}
