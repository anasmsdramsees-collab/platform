import type { Metadata } from "next";
import { isLocale, type Locale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n/get-dictionary";
import { InfoCard } from "@/components/ui/info-card";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const s = getDictionary(locale).servicesPage;
  return { title: `${s.eyebrow} | Syltra One`, description: s.subtitle };
}

export default async function ServicesPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const s = getDictionary(locale).servicesPage;

  return (
    <>
      {/* Services */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-6xl px-5 py-24 sm:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <p className="font-mono text-[12px] uppercase tracking-[0.14em] text-slate">{s.eyebrow}</p>
            <h1 className="font-display mt-3 text-balance text-4xl font-bold text-platinum sm:text-5xl">
              {s.title}
            </h1>
            <p className="mt-5 text-chrome-dim">{s.subtitle}</p>
          </div>

          <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {s.items.map((item, i) => (
              <InfoCard key={item.name}>
                <p className="font-mono text-xs text-ion">{String(i + 1).padStart(2, "0")}</p>
                <p className="mt-3 font-semibold leading-snug text-platinum">{item.name}</p>
                <p className="mt-2.5 text-sm leading-relaxed text-chrome-dim">{item.desc}</p>
              </InfoCard>
            ))}
          </div>
        </div>
      </section>

      {/* Field services */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-5xl px-5 py-20 sm:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <p className="font-mono text-[12px] uppercase tracking-[0.14em] text-slate">{s.field.eyebrow}</p>
            <h2 className="font-display mt-3 text-balance text-3xl font-bold text-platinum sm:text-4xl">
              {s.field.title}
            </h2>
            <p className="mt-4 text-chrome-dim">{s.field.subtitle}</p>
          </div>
          <div className="mt-12 grid gap-4 sm:grid-cols-3">
            {s.field.items.map((item) => (
              <InfoCard key={item.name}>
                <p className="font-mono text-sm font-semibold text-platinum">{item.name}</p>
                <p className="mt-2.5 text-sm leading-relaxed text-chrome-dim">{item.desc}</p>
              </InfoCard>
            ))}
          </div>
        </div>
      </section>

      {/* Delivery model */}
      <section>
        <div className="mx-auto max-w-5xl px-5 py-20 sm:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <p className="font-mono text-[12px] uppercase tracking-[0.14em] text-slate">{s.delivery.eyebrow}</p>
            <h2 className="font-display mt-3 text-balance text-3xl font-bold text-platinum sm:text-4xl">
              {s.delivery.title}
            </h2>
            <p className="mt-4 text-chrome-dim">{s.delivery.subtitle}</p>
          </div>

          <ol className="mt-12 grid gap-4 sm:grid-cols-3 lg:grid-cols-5">
            {s.delivery.stages.map((stage, i) => (
              <InfoCard key={stage.code} className="text-center">
                <p className="font-mono text-2xl font-medium text-ion">{i + 1}</p>
                <p className="mt-2 font-mono text-[12px] font-semibold tracking-wide text-platinum">
                  {stage.code}
                </p>
                <p className="mt-2 text-xs leading-relaxed text-chrome-dim">{stage.desc}</p>
              </InfoCard>
            ))}
          </ol>

          <div className="mt-4 grid gap-4 sm:grid-cols-3">
            {s.delivery.commitments.map((c) => (
              <InfoCard key={c.name}>
                <p className="font-semibold leading-snug text-platinum">{c.name}</p>
                <p className="mt-2.5 text-sm leading-relaxed text-chrome-dim">{c.desc}</p>
              </InfoCard>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
