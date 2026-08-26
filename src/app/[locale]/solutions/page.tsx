import type { Metadata } from "next";
import Link from "next/link";
import { isLocale, type Locale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n/get-dictionary";
import { InfoCard } from "@/components/ui/info-card";
import { pageMetadata } from "@/lib/seo";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const s = getDictionary(locale).solutionsPage;
  return pageMetadata({ locale, path: "/solutions", title: `${s.eyebrow} | Syltra Life`, description: s.subtitle });
}

export default async function SolutionsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const s = getDictionary(locale).solutionsPage;

  return (
    <>
      {/* Four divisions */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-6xl px-5 py-24 sm:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <p className="font-mono text-[12px] uppercase tracking-[0.14em] text-slate">{s.eyebrow}</p>
            <h1 className="font-display mt-3 text-balance text-4xl font-bold text-platinum sm:text-5xl">
              {s.title}
            </h1>
            <p className="mt-5 text-chrome-dim">{s.subtitle}</p>
          </div>

          <div className="mt-14 space-y-4">
            {s.divisions.map((d) => (
              <InfoCard key={d.code} className="sm:p-8">
                <div className="grid gap-6 lg:grid-cols-[minmax(0,18rem)_1fr] lg:gap-10">
                  <div>
                    <p className="font-mono text-[12px] font-semibold tracking-[0.14em] text-ion">
                      {d.code}
                    </p>
                    <p className="font-display mt-2 text-xl font-bold text-platinum">{d.name}</p>
                    <p className="mt-2.5 text-sm leading-relaxed text-chrome-dim">{d.desc}</p>
                  </div>

                  <ul className="grid gap-x-8 gap-y-5 sm:grid-cols-2">
                    {d.points.map((p) => (
                      <li key={p.name}>
                        <p className="text-sm font-semibold text-platinum">{p.name}</p>
                        <p className="mt-1.5 text-sm leading-relaxed text-chrome-dim">{p.desc}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              </InfoCard>
            ))}
          </div>

          <p className="mt-6 text-center text-xs leading-relaxed text-slate">{s.healthNote}</p>
        </div>
      </section>

      {/* Sector solutions */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-5xl px-5 py-20 sm:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <p className="font-mono text-[12px] uppercase tracking-[0.14em] text-slate">
              {s.sectors.eyebrow}
            </p>
            <h2 className="font-display mt-3 text-balance text-3xl font-bold text-platinum sm:text-4xl">
              {s.sectors.title}
            </h2>
          </div>

          <div className="mt-12 overflow-x-auto rounded-2xl border border-hairline bg-graphite/70">
            <table className="w-full min-w-[36rem] text-start text-sm">
              <thead>
                <tr className="border-b border-hairline">
                  <th className="px-5 py-4 text-start font-mono text-[11px] uppercase tracking-widest text-slate sm:px-6">
                    {s.sectors.columns.sector}
                  </th>
                  <th className="px-5 py-4 text-start font-mono text-[11px] uppercase tracking-widest text-slate sm:px-6">
                    {s.sectors.columns.need}
                  </th>
                  <th className="px-5 py-4 text-start font-mono text-[11px] uppercase tracking-widest text-slate sm:px-6">
                    {s.sectors.columns.units}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-hairline">
                {s.sectors.rows.map((row) => (
                  <tr key={row.sector}>
                    <td className="px-5 py-4 font-semibold text-platinum sm:px-6">{row.sector}</td>
                    <td className="px-5 py-4 text-chrome-dim sm:px-6">{row.need}</td>
                    <td className="whitespace-nowrap px-5 py-4 font-mono text-[12.5px] text-ion sm:px-6">
                      {row.units}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="mt-6 text-center text-sm text-chrome-dim">{s.sectors.note}</p>
        </div>
      </section>

      {/* Trust by design */}
      <section>
        <div className="mx-auto max-w-5xl px-5 py-20 sm:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <p className="font-mono text-[12px] uppercase tracking-[0.14em] text-slate">
              {s.trust.eyebrow}
            </p>
            <h2 className="font-display mt-3 text-balance text-3xl font-bold text-platinum sm:text-4xl">
              {s.trust.title}
            </h2>
          </div>

          <div className="mt-12 grid gap-4 sm:grid-cols-2">
            {s.trust.items.map((item) => (
              <InfoCard key={item.name}>
                <p className="font-semibold leading-snug text-platinum">{item.name}</p>
                <p className="mt-2.5 text-sm leading-relaxed text-chrome-dim">{item.desc}</p>
              </InfoCard>
            ))}
          </div>

          <div className="mt-10 text-center">
            <p className="font-mono text-[11px] uppercase tracking-widest text-slate">
              {s.trust.principlesLabel}
            </p>
            <ul className="mt-4 flex flex-wrap justify-center gap-2">
              {s.trust.principles.map((p) => (
                <li
                  key={p}
                  className="rounded-full border border-hairline bg-graphite/70 px-3.5 py-1.5 text-[12.5px] text-chrome-dim"
                >
                  {p}
                </li>
              ))}
            </ul>
          </div>

          <p className="mx-auto mt-8 max-w-2xl text-center text-sm leading-relaxed text-chrome-dim">
            {s.trust.note}
          </p>
        </div>
      </section>

      <section className="border-t border-hairline">
        <div className="mx-auto max-w-3xl px-5 py-20 text-center sm:px-8">
          <h2 className="font-display text-balance text-3xl font-bold text-platinum sm:text-4xl">
            {locale === "ar" ? "ابدأ بمعاينة مجانية." : "Start with a free site survey."}
          </h2>
          <p className="mt-4 text-chrome-dim">
            {locale === "ar"
              ? "نزور الموقع، نقيس الاحتياج، ونرسل لك عرض سعر مفصّلًا بدون أي التزام."
              : "We visit the site, measure the need, and send you an itemised quote with no commitment."}
          </p>
          <Link
            href={`/${locale}/quote`}
            className="mt-8 inline-block rounded-md bg-platinum px-7 py-3 text-sm font-semibold text-void transition-opacity hover:opacity-90"
          >
            {locale === "ar" ? "احجز معاينة" : "Book a survey"}
          </Link>
        </div>
      </section>
    </>
  );
}
