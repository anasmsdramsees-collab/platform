import type { Metadata } from "next";
import Link from "next/link";
import Image from "next/image";
import { isLocale, type Locale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n/get-dictionary";
import { pageMetadata } from "@/lib/seo";
import { DIVISIONS, divisionName } from "@/lib/divisions";
import { assetPath } from "@/lib/base-path";
import VisionBand from "@/components/vision-band";

/** Syltra One umbrella accent, silver. */
const ONE = "#BFC6D0";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const dict = getDictionary(locale);
  return pageMetadata({ locale, path: "/about", title: dict.meta.titleAbout, description: dict.meta.description });
}

export default async function AboutPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const dict = getDictionary(locale);
  const a = dict.aboutPage;

  return (
    <div>
      {/* Hero */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-4xl px-5 py-20 text-center sm:px-8">
          <p className="font-mono text-[12px] tracking-[0.14em] text-slate uppercase">
            {a.hero.eyebrow}
          </p>
          <h1 className="font-display mt-3 text-balance text-4xl font-bold text-platinum sm:text-5xl">
            {a.hero.title}
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-chrome-dim">{a.hero.subtitle}</p>
        </div>
      </section>

      {/* Facts strip */}
      <section className="border-b border-hairline">
        <div className="mx-auto grid max-w-6xl grid-cols-2 border-s border-t border-hairline px-0 sm:grid-cols-4">
          {a.facts.map((fact) => (
            <div key={fact.label} className="border-b border-e border-hairline px-5 py-9 text-center">
              <p className="font-display text-2xl font-bold sm:text-3xl" style={{ color: ONE }}>{fact.value}</p>
              <p className="mt-2 text-xs text-chrome-dim sm:text-sm">{fact.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Story */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-3xl px-5 py-20 sm:px-8">
          <p className="font-mono text-[12px] tracking-[0.14em] text-slate uppercase">
            {a.story.eyebrow}
          </p>
          <h2 className="font-display mt-3 text-3xl font-bold text-platinum sm:text-4xl">
            {a.story.title}
          </h2>
          <div className="mt-8 space-y-5 text-chrome-dim">
            {a.story.paragraphs.map((p, i) => (
              <p key={i}>{p}</p>
            ))}
          </div>
        </div>
      </section>

      {/* Mission / Vision */}
      <section className="border-b border-hairline">
        <div className="mx-auto grid max-w-6xl grid-cols-1 gap-x-12 gap-y-12 px-5 py-20 sm:grid-cols-2 sm:px-8">
          <div>
            <span className="block h-px w-10" style={{ background: ONE }} aria-hidden />
            <p className="mt-5 font-mono text-[11px] uppercase tracking-widest text-slate">{a.mission.label}</p>
            <p className="font-display mt-4 text-balance text-xl font-semibold leading-relaxed text-platinum sm:text-2xl">
              {a.mission.text}
            </p>
          </div>
          <div>
            <span className="block h-px w-10" style={{ background: ONE }} aria-hidden />
            <p className="mt-5 font-mono text-[11px] uppercase tracking-widest text-slate">{a.vision.label}</p>
            <p className="font-display mt-4 text-balance text-xl font-semibold leading-relaxed text-platinum sm:text-2xl">
              {a.vision.text}
            </p>
          </div>
        </div>
      </section>

      {/* Divisions */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-6xl px-5 py-20 sm:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <p className="font-mono text-[12px] tracking-[0.14em] uppercase" style={{ color: ONE }}>
              {locale === "ar" ? "الأقسام" : "Divisions"}
            </p>
            <h2 className="font-display mt-3 text-balance text-3xl font-bold text-platinum sm:text-4xl">
              {locale === "ar" ? "خمسة أقسام تحت مظلة واحدة." : "Five divisions under one umbrella."}
            </h2>
          </div>
          <div className="mt-12 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {DIVISIONS.map((d) => (
              <Link
                key={d.key}
                href={`/${locale}${d.href}`}
                className="group flex items-center gap-4 py-3"
              >
                <div
                  className="relative h-16 w-24 flex-none overflow-hidden border-s-2"
                  style={{ borderColor: d.color }}
                >
                  <Image
                    src={assetPath(d.image)}
                    alt={divisionName(d, locale)}
                    fill
                    sizes="96px"
                    className="object-cover transition-transform duration-700 group-hover:scale-105"
                  />
                </div>
                <div>
                  <p className="font-display font-bold text-platinum transition-opacity group-hover:opacity-80">
                    {divisionName(d, locale)}
                  </p>
                  <p className="mt-0.5 font-mono text-[11px] text-slate">
                    {locale === "ar" ? d.label.ar : d.label.en}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-6xl px-5 py-20 sm:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <p className="font-mono text-[12px] tracking-[0.14em] text-slate uppercase">
              {a.values.eyebrow}
            </p>
            <h2 className="font-display mt-3 text-3xl font-bold text-platinum sm:text-4xl">
              {a.values.title}
            </h2>
          </div>
          <div className="mt-12 grid grid-cols-1 gap-x-8 gap-y-9 sm:grid-cols-2 lg:grid-cols-3">
            {a.values.items.map((v) => (
              <div key={v.name} className="border-t border-hairline pt-5">
                <span className="block h-px w-8" style={{ background: ONE }} aria-hidden />
                <p className="mt-4 font-semibold text-platinum">{v.name}</p>
                <p className="mt-2.5 text-sm leading-relaxed text-chrome-dim">{v.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Chairman */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-3xl px-5 py-20 sm:px-8">
          <p className="text-center font-mono text-[12px] tracking-[0.14em] text-slate uppercase">
            {a.chairman.eyebrow}
          </p>
          <div className="mt-10 text-center">
            <blockquote className="font-display text-balance text-2xl font-medium leading-relaxed text-platinum sm:text-3xl">
              “{a.chairman.quote}”
            </blockquote>
            <p className="mt-8 font-mono text-[12px] uppercase tracking-widest text-slate">{a.chairman.role}</p>
          </div>
        </div>
      </section>

      {/* Vision 2030 */}
      <VisionBand locale={locale} />

      {/* Roadmap */}
      <section>
        <div className="mx-auto max-w-3xl px-5 py-20 sm:px-8">
          <p className="font-mono text-[12px] tracking-[0.14em] text-slate uppercase">
            {a.roadmap.eyebrow}
          </p>
          <h2 className="font-display mt-3 text-3xl font-bold text-platinum sm:text-4xl">
            {a.roadmap.title}
          </h2>
          <div className="mt-10 border-t border-hairline">
            {a.roadmap.items.map((item) => (
              <div key={item.year} className="flex items-baseline gap-6 border-b border-hairline py-5">
                <span className="font-display text-lg font-bold tabular-nums" style={{ color: ONE }}>{item.year}</span>
                <p className="text-sm leading-relaxed text-chrome-dim">{item.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
