import Link from "next/link";
import Image from "next/image";
import { notFound } from "next/navigation";
import type { Locale } from "@/lib/i18n/config";
import { DIVISIONS, divisionName } from "@/lib/divisions";
import { DIVISION_CONTENT, pick } from "@/lib/division-content";
import { assetPath } from "@/lib/base-path";

export function findService(divisionKey: string, slug: string) {
  const division = DIVISIONS.find((d) => d.key === divisionKey);
  const content = DIVISION_CONTENT[divisionKey as keyof typeof DIVISION_CONTENT];
  const service = content?.systems.find((s) => s.slug === slug);
  if (!division || !content || !service) return null;
  return { division, content, service };
}

export default function ServiceDetail({
  divisionKey,
  slug,
  locale,
}: {
  divisionKey: string;
  slug: string;
  locale: Locale;
}) {
  const found = findService(divisionKey, slug);
  if (!found) notFound();
  const { division, content, service } = found;
  const accent = division.color;
  const dName = divisionName(division, locale);
  const related = content.systems.filter((s) => s.slug && s.slug !== slug);

  const ld = [
    {
      "@context": "https://schema.org",
      "@type": "Service",
      name: `${pick(service.title, locale)} — ${dName}`,
      serviceType: service.en || pick(service.title, locale),
      provider: { "@type": "Organization", name: "Syltra One" },
      areaServed: "SA",
      description: service.lead ? pick(service.lead, locale) : undefined,
    },
    {
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      itemListElement: [
        { "@type": "ListItem", position: 1, name: dName, item: `/${locale}${division.href}` },
        { "@type": "ListItem", position: 2, name: pick(service.title, locale) },
      ],
    },
  ];

  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-hairline">
        {service.img ? (
          <div className="absolute inset-0">
            <Image src={assetPath(service.img)} alt={pick(service.title, locale)} fill priority sizes="100vw" className="object-cover" />
            <div
              className="absolute inset-0"
              style={{ background: `linear-gradient(${locale === "ar" ? 270 : 90}deg, rgba(11,12,14,0.94) 0%, rgba(11,12,14,0.8) 34%, rgba(11,12,14,0.25) 70%)` }}
            />
          </div>
        ) : null}
        <div className="relative z-10 mx-auto max-w-5xl px-5 py-24 sm:px-8 sm:py-32">
          <nav className="flex items-center gap-2 font-mono text-[11px] text-slate">
            <Link href={`/${locale}${division.href}`} className="transition-colors hover:text-platinum" style={{ color: accent }}>
              {dName}
            </Link>
            <span aria-hidden>/</span>
            <span>{pick(service.title, locale)}</span>
          </nav>
          <h1 className="font-display mt-4 max-w-3xl text-balance text-4xl font-bold leading-[1.12] text-platinum sm:text-5xl">
            {pick(service.title, locale)}
          </h1>
          {service.lead ? (
            <p className="mt-6 max-w-2xl text-balance text-base leading-relaxed text-chrome-dim sm:text-lg">
              {pick(service.lead, locale)}
            </p>
          ) : null}
          <div className="mt-9 flex flex-wrap items-center gap-4">
            <Link
              href={`/${locale}/contact`}
              className="rounded-md px-7 py-3 text-sm font-semibold text-void transition-opacity hover:opacity-90"
              style={{ background: accent }}
            >
              {locale === "ar" ? "اطلب عرض سعر" : "Request a quote"}
            </Link>
            <a href="tel:0550098550" className="rounded-md border border-hairline-strong px-7 py-3 font-mono text-sm font-semibold text-platinum transition-colors hover:border-ion">
              0550098550
            </a>
          </div>
        </div>
      </section>

      {/* Overview */}
      {service.body?.length ? (
        <section className="border-b border-hairline">
          <div className="mx-auto max-w-3xl px-5 py-20 sm:px-8">
            <p className="font-mono text-[12px] uppercase tracking-[0.14em] text-slate">
              {locale === "ar" ? "نظرة عامة" : "Overview"}
            </p>
            <div className="mt-6 space-y-5 text-[15px] leading-[1.9] text-chrome-dim sm:text-base">
              {service.body.map((para, i) => (
                <p key={i}>{pick(para, locale)}</p>
              ))}
            </div>
          </div>
        </section>
      ) : null}

      {/* Points */}
      {service.points?.length ? (
        <section className="border-b border-hairline">
          <div className="mx-auto max-w-5xl px-5 py-20 sm:px-8">
            <p className="font-mono text-[12px] uppercase tracking-[0.14em] text-slate">
              {locale === "ar" ? "ما نقدّمه" : "What we offer"}
            </p>
            <div className="mt-10 grid grid-cols-1 border-t border-hairline sm:grid-cols-2">
              {service.points.map((p, i) => (
                <div key={i} className="flex gap-4 border-b border-hairline py-6 pe-6">
                  <span className="mt-1 h-2 w-2 flex-none rounded-full" style={{ background: accent }} aria-hidden />
                  <p className="leading-relaxed text-chrome-dim">{pick(p, locale)}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      ) : null}

      {/* Applications */}
      {service.useCases?.length ? (
        <section className="border-b border-hairline">
          <div className="mx-auto max-w-5xl px-5 py-20 sm:px-8">
            <p className="font-mono text-[12px] uppercase tracking-[0.14em] text-slate">
              {locale === "ar" ? "أين يناسب" : "Where it fits"}
            </p>
            <div className="mt-8 grid grid-cols-1 border-s border-t border-hairline sm:grid-cols-2">
              {service.useCases.map((u, i) => (
                <div key={i} className="flex items-center gap-3 border-b border-e border-hairline p-5">
                  <span className="h-1.5 w-1.5 flex-none rounded-full" style={{ background: accent }} aria-hidden />
                  <p className="font-medium text-platinum">{pick(u, locale)}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      ) : null}

      {/* Related services */}
      {related.length ? (
        <section className="border-b border-hairline">
          <div className="mx-auto max-w-6xl px-5 py-20 sm:px-8">
            <p className="font-mono text-[12px] uppercase tracking-[0.14em] text-slate">
              {locale === "ar" ? `المزيد من ${dName}` : `More from ${dName}`}
            </p>
            <div className="mt-8 grid grid-cols-2 gap-x-5 gap-y-8 sm:grid-cols-3 lg:grid-cols-4">
              {related.map((s, i) => (
                <Link key={i} href={`/${locale}${division.href}/${s.slug}`} className="group">
                  {s.img ? (
                    <div className="relative aspect-[4/3] overflow-hidden">
                      <Image src={assetPath(s.img)} alt={pick(s.title, locale)} fill sizes="(max-width:640px) 50vw, 25vw" className="object-cover transition-transform duration-700 group-hover:scale-[1.03]" />
                    </div>
                  ) : null}
                  <span className="mt-3 block h-px w-8 transition-[width] duration-500 group-hover:w-14" style={{ background: accent }} aria-hidden />
                  <p className="mt-3 font-semibold leading-snug text-platinum">{pick(s.title, locale)}</p>
                </Link>
              ))}
            </div>
          </div>
        </section>
      ) : null}

      {/* CTA */}
      <section>
        <div className="mx-auto max-w-3xl px-5 py-24 text-center sm:px-8">
          <h2 className="font-display text-balance text-3xl font-bold text-platinum sm:text-4xl">
            {locale === "ar" ? "ابدأ بمعاينة ودراسة." : "Start with a survey and study."}
          </h2>
          <p className="mt-4 text-chrome-dim">
            {locale === "ar"
              ? "نحدّد الأنسب لمشروعك ونجهّز عرضًا واضحًا للتوريد والتنفيذ والصيانة."
              : "We identify the best fit for your project and prepare a clear proposal for supply, execution and maintenance."}
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link href={`/${locale}/contact`} className="rounded-md px-7 py-3 text-sm font-semibold text-void transition-opacity hover:opacity-90" style={{ background: accent }}>
              {locale === "ar" ? "تواصل معنا" : "Contact us"}
            </Link>
            <Link href={`/${locale}${division.href}`} className="rounded-md border border-hairline-strong px-7 py-3 text-sm font-semibold text-platinum transition-colors hover:border-ion">
              {locale === "ar" ? `كل خدمات ${dName}` : `All ${dName} services`}
            </Link>
          </div>
        </div>
      </section>

      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(ld) }} />
    </>
  );
}
