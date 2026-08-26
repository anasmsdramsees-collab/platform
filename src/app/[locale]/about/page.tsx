import type { Metadata } from "next";
import { InfoCard } from "@/components/ui/info-card";
import { isLocale, type Locale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n/get-dictionary";
import { pageMetadata } from "@/lib/seo";

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
        <div className="mx-auto grid max-w-6xl grid-cols-2 gap-4 px-5 py-10 sm:grid-cols-4 sm:px-8">
          {a.facts.map((fact) => (
            <InfoCard key={fact.label} className="px-5 py-8 text-center">
              <p className="font-mono text-xl font-medium text-ion sm:text-2xl">{fact.value}</p>
              <p className="mt-2 text-xs text-chrome-dim sm:text-sm">{fact.label}</p>
            </InfoCard>
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
        <div className="mx-auto grid max-w-6xl grid-cols-1 gap-4 px-5 py-16 sm:grid-cols-2 sm:px-8">
          <InfoCard className="p-8 sm:p-10">
            <p className="font-mono text-[11px] uppercase tracking-widest text-slate">
              {a.mission.label}
            </p>
            <p className="font-display mt-4 text-balance text-xl font-semibold text-platinum sm:text-2xl">
              {a.mission.text}
            </p>
          </InfoCard>
          <InfoCard className="p-8 sm:p-10">
            <p className="font-mono text-[11px] uppercase tracking-widest text-slate">
              {a.vision.label}
            </p>
            <p className="font-display mt-4 text-balance text-xl font-semibold text-platinum sm:text-2xl">
              {a.vision.text}
            </p>
          </InfoCard>
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
          <div className="mt-12 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {a.values.items.map((v, i) => (
              <InfoCard key={v.name}>
                <p className="font-mono text-xs text-ion">{String(i + 1).padStart(2, "0")}</p>
                <p className="mt-3 font-semibold text-platinum">{v.name}</p>
                <p className="mt-2.5 text-sm leading-relaxed text-chrome-dim">{v.desc}</p>
              </InfoCard>
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
          <InfoCard className="mt-8 p-8 text-center sm:p-12">
            <blockquote className="font-display text-balance text-xl font-medium leading-relaxed text-platinum sm:text-2xl">
              “{a.chairman.quote}”
            </blockquote>
            <div className="mt-8">
              <p className="text-sm text-chrome-dim">{a.chairman.role}</p>
            </div>
          </InfoCard>
        </div>
      </section>

      {/* Roadmap */}
      <section>
        <div className="mx-auto max-w-3xl px-5 py-20 sm:px-8">
          <p className="font-mono text-[12px] tracking-[0.14em] text-slate uppercase">
            {a.roadmap.eyebrow}
          </p>
          <h2 className="font-display mt-3 text-3xl font-bold text-platinum sm:text-4xl">
            {a.roadmap.title}
          </h2>
          <div className="mt-10 grid gap-4 sm:grid-cols-2">
            {a.roadmap.items.map((item) => (
              <InfoCard key={item.year}>
                <span className="font-mono text-xs text-ion">{item.year}</span>
                <p className="mt-2.5 text-sm leading-relaxed text-chrome-dim">{item.text}</p>
              </InfoCard>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
