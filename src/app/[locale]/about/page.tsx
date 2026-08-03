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
  return { title: dict.meta.titleAbout, description: dict.meta.description };
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
        <div className="mx-auto grid max-w-6xl grid-cols-2 gap-px overflow-hidden bg-hairline sm:grid-cols-4">
          {a.facts.map((fact) => (
            <div key={fact.label} className="bg-void px-5 py-10 text-center">
              <p className="font-mono text-xl font-medium text-ion sm:text-2xl">{fact.value}</p>
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
        <div className="mx-auto grid max-w-6xl grid-cols-1 gap-px overflow-hidden bg-hairline sm:grid-cols-2">
          <div className="bg-void p-10 sm:p-12">
            <p className="font-mono text-[11px] uppercase tracking-widest text-slate">
              {a.mission.label}
            </p>
            <p className="font-display mt-4 text-balance text-xl font-semibold text-platinum sm:text-2xl">
              {a.mission.text}
            </p>
          </div>
          <div className="bg-void p-10 sm:p-12">
            <p className="font-mono text-[11px] uppercase tracking-widest text-slate">
              {a.vision.label}
            </p>
            <p className="font-display mt-4 text-balance text-xl font-semibold text-platinum sm:text-2xl">
              {a.vision.text}
            </p>
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
          <div className="mt-12 grid grid-cols-1 gap-px overflow-hidden bg-hairline sm:grid-cols-2 lg:grid-cols-3">
            {a.values.items.map((v, i) => (
              <div key={v.name} className="bg-void p-6">
                <p className="font-mono text-xs text-ion">{String(i + 1).padStart(2, "0")}</p>
                <p className="mt-3 font-semibold text-platinum">{v.name}</p>
                <p className="mt-2 text-sm text-chrome-dim">{v.desc}</p>
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
          <blockquote className="font-display mt-6 text-balance text-center text-xl font-medium leading-relaxed text-platinum sm:text-2xl">
            “{a.chairman.quote}”
          </blockquote>
          <div className="mt-8 text-center">
            <p className="font-semibold text-platinum">{a.chairman.name}</p>
            <p className="mt-1 text-sm text-chrome-dim">{a.chairman.role}</p>
          </div>
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
          <div className="mt-10 divide-y divide-hairline border-y border-hairline">
            {a.roadmap.items.map((item) => (
              <div key={item.year} className="flex items-baseline gap-6 py-5">
                <span className="font-mono text-sm text-ion">{item.year}</span>
                <p className="text-sm text-chrome-dim">{item.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
