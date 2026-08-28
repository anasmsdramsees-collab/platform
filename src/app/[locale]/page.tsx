import Link from "next/link";
import Image from "next/image";
import type { Metadata } from "next";
import { isLocale, type Locale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n/get-dictionary";
import ParticlesBg from "@/components/ui/particles-bg";
import { HeroCarousel } from "@/components/ui/hero-carousel";
import { HoverBorderGradientLink } from "@/components/hover-border-gradient";
import { assetPath } from "@/lib/base-path";
import { pageMetadata } from "@/lib/seo";
import { DIVISIONS, divisionName } from "@/lib/divisions";
import VisionBand from "@/components/vision-band";
import FaqSection from "@/components/faq-section";
import { GENERAL_FAQ } from "@/lib/faq";
import { POSTS, bt } from "@/lib/blog";

/** Syltra One umbrella accent, silver. */
const ONE = "#BFC6D0";

const T = {
  ar: {
    eyebrow: "منظومة واحدة · ذكاء متصل",
    title: "منظومة واحدة تربط الحياة والأعمال.",
    subtitle:
      "سيلترا وان شركة تقنية سعودية توحّد الحياة الذكية والبرمجيات والتكييف والأمن والمصاعد تحت علامة واحدة ومعايير واضحة.",
    ctaExplore: "استكشف الأقسام",
    ctaAbout: "من نحن",
    divisionsEyebrow: "الأقسام",
    divisionsTitle: "خمسة أقسام. مظلة واحدة.",
    divisionsSub: "كل قسم متخصص في مجاله، ومتكامل مع البقية تحت هوية ومعايير سيلترا وان.",
    discover: "اكتشف القسم",
    whyEyebrow: "لماذا شركة واحدة",
    whyTitle: "تكامل حقيقي، لا موردون متفرقون.",
    why: [
      { n: "01", t: "مسؤولية واحدة", d: "جهة واحدة تدير التصميم والتنفيذ والصيانة عبر كل الأنظمة." },
      { n: "02", t: "معايير موحّدة", d: "الجودة والتوثيق والدعم بنفس المستوى في كل قسم." },
      { n: "03", t: "أنظمة تتحدّث مع بعضها", d: "المنزل والتكييف والأمن والمصاعد في منظومة واحدة متكاملة." },
    ],
    ctaTitle: "عندك مشروع يشمل أكثر من قسم؟",
    ctaSub: "نجمع أقسام سيلترا وان في خطة واحدة واضحة، من الدراسة حتى التشغيل والصيانة.",
    ctaBtn: "تواصل معنا",
  },
  en: {
    eyebrow: "One Group · Connected Intelligence",
    title: "One group that connects living and business.",
    subtitle:
      "Syltra One is a Saudi technology group uniting smart living, software, HVAC, security and elevators under one brand and clear standards.",
    ctaExplore: "Explore divisions",
    ctaAbout: "About us",
    divisionsEyebrow: "Divisions",
    divisionsTitle: "Five divisions. One umbrella.",
    divisionsSub: "Each division is a specialist in its field, integrated with the rest under Syltra One's identity and standards.",
    discover: "Explore division",
    whyEyebrow: "Why one company",
    whyTitle: "Real integration, not scattered vendors.",
    why: [
      { n: "01", t: "One accountability", d: "A single party owning design, execution and maintenance across every system." },
      { n: "02", t: "Unified standards", d: "Quality, documentation and support at the same level in every division." },
      { n: "03", t: "Systems that talk", d: "Home, climate, security and elevators in one integrated ecosystem." },
    ],
    ctaTitle: "A project that spans more than one division?",
    ctaSub: "We bring Syltra One's divisions into one clear plan, from study to operation and maintenance.",
    ctaBtn: "Contact us",
  },
} as const;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const t = T[locale];
  return pageMetadata({ locale, path: "", title: `Syltra One | ${t.title}`, description: t.subtitle });
}

export default async function HomePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const t = T[locale];

  // A showcase hero slider for Syltra One: a few cinematic frames pulled from
  // each division, ordered to alternate scene and colour.
  const heroPicks: { div: string; img: string }[] = [
    { div: "life", img: "/divisions/life.jpg" },
    { div: "climate", img: "/divisions/climate.jpg" },
    { div: "glide", img: "/divisions/glide.jpg" },
    { div: "shield", img: "/divisions/shield.jpg" },
    { div: "os", img: "/divisions/os-1.jpg" },
    { div: "climate", img: "/divisions/climate-2.jpg" },
    { div: "glide", img: "/divisions/glide-2.jpg" },
    { div: "shield", img: "/divisions/shield-1.jpg" },
    { div: "os", img: "/divisions/os-2.jpg" },
  ];
  const heroSlides = heroPicks.map(({ div, img }) => {
    const d = DIVISIONS.find((x) => x.key === div)!;
    return {
      src: img,
      label: divisionName(d, locale),
      title: locale === "ar" ? d.label.ar : d.label.en,
      caption: locale === "ar" ? d.tagline.ar : d.tagline.en,
    };
  });

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
          style={{
            background:
              "radial-gradient(65% 55% at 50% 0%, rgba(11,12,14,0.18), rgba(11,12,14,0.62) 75%)",
          }}
        />
        <div className="relative z-20 mx-auto max-w-4xl px-5 py-24 text-center sm:px-8 sm:py-32">
          <div dir="ltr" className="mx-auto mb-6 flex items-center justify-center gap-2.5">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={assetPath("/brand/divisions/word.png")} alt="SYLTRA" className="h-6 w-auto sm:h-7" />
            <span className="h-5 w-px" style={{ background: ONE }} />
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={assetPath("/brand/divisions/one.png")} alt="ONE" className="h-6 w-auto sm:h-7" />
          </div>
          <p className="font-mono text-[12px] tracking-[0.14em] uppercase" style={{ color: ONE }}>{t.eyebrow}</p>
          <h1 className="font-display mt-5 text-balance text-4xl font-bold leading-[1.1] text-platinum sm:text-6xl">
            {t.title}
          </h1>
          <p className="mx-auto mt-6 max-w-xl text-balance text-base text-chrome-dim sm:text-lg">
            {t.subtitle}
          </p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <HoverBorderGradientLink href={`/${locale}#divisions`} className="bg-[#BFC6D0] text-void" containerClassName="gap-0">
              {t.ctaExplore}
            </HoverBorderGradientLink>
            <HoverBorderGradientLink href={`/${locale}/about`} className="bg-void text-platinum" containerClassName="gap-0">
              {t.ctaAbout}
            </HoverBorderGradientLink>
          </div>
        </div>

        {/* Hero carousel, divisions */}
        <div className="relative z-0 mt-4 w-full sm:mt-10">
          <HeroCarousel slides={heroSlides} rtl={locale === "ar"} />
        </div>
      </section>

      {/* Divisions grid */}
      <section id="divisions" className="border-b border-hairline scroll-mt-24">
        <div className="mx-auto max-w-6xl px-5 py-24 sm:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <p className="font-mono text-[12px] tracking-[0.14em] text-slate uppercase">{t.divisionsEyebrow}</p>
            <h2 className="font-display mt-3 text-balance text-3xl font-bold text-platinum sm:text-4xl">
              {t.divisionsTitle}
            </h2>
            <p className="mt-4 text-chrome-dim">{t.divisionsSub}</p>
          </div>
          <div className="mt-14 grid grid-cols-1 gap-x-8 gap-y-12 sm:grid-cols-2 lg:grid-cols-3">
            {DIVISIONS.map((d) => (
              <Link key={d.key} href={`/${locale}${d.href}`} className="group block">
                <div className="relative aspect-[16/10] overflow-hidden">
                  <Image
                    src={assetPath(d.image)}
                    alt={divisionName(d, locale)}
                    fill
                    sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
                    className="object-cover transition-transform duration-[900ms] ease-out group-hover:scale-[1.03]"
                  />
                </div>
                <div className="mt-4">
                  <span
                    className="block h-px w-8 transition-[width] duration-500 group-hover:w-14"
                    style={{ background: d.color }}
                    aria-hidden
                  />
                  <p className="font-display mt-4 text-lg font-bold text-platinum">{divisionName(d, locale)}</p>
                  <p className="mt-1 font-mono text-[11px] uppercase tracking-widest text-slate">
                    {locale === "ar" ? d.label.ar : d.label.en}
                  </p>
                  <p className="mt-3 text-sm leading-relaxed text-chrome-dim">
                    {locale === "ar" ? d.tagline.ar : d.tagline.en}
                  </p>
                  <span
                    className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold transition-opacity group-hover:opacity-80"
                    style={{ color: d.color }}
                  >
                    {t.discover}
                    <span aria-hidden>{locale === "ar" ? "←" : "→"}</span>
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Why one company */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-4xl px-5 py-20 sm:px-8">
          <p className="text-center font-mono text-[12px] tracking-[0.14em] text-slate uppercase">{t.whyEyebrow}</p>
          <h2 className="font-display mt-3 text-balance text-center text-3xl font-bold text-platinum sm:text-4xl">
            {t.whyTitle}
          </h2>
          <div className="mt-12 grid gap-4 sm:grid-cols-3">
            {t.why.map((w) => (
              <div key={w.n} className="rounded-lg border border-hairline p-6">
                <span className="font-mono text-xs" style={{ color: ONE }}>{w.n}</span>
                <p className="mt-3 font-semibold leading-snug text-platinum">{w.t}</p>
                <p className="mt-2.5 text-sm leading-relaxed text-chrome-dim">{w.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Latest from the blog */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-6xl px-5 py-24 sm:px-8">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="font-mono text-[12px] uppercase tracking-[0.14em] text-slate">
                {locale === "ar" ? "من المدونة" : "From the blog"}
              </p>
              <h2 className="font-display mt-3 text-3xl font-bold text-platinum sm:text-4xl">
                {locale === "ar" ? "أحدث الأدلّة والمقالات." : "Latest guides and articles."}
              </h2>
            </div>
            <Link href={`/${locale}/blog`} className="font-mono text-sm transition-opacity hover:opacity-80" style={{ color: ONE }}>
              {locale === "ar" ? "كل المقالات ←" : "All articles →"}
            </Link>
          </div>
          <div className="mt-12 grid grid-cols-1 gap-x-8 gap-y-10 sm:grid-cols-2 lg:grid-cols-3">
            {[...POSTS].sort((a, b) => (a.date < b.date ? 1 : -1)).slice(0, 3).map((post) => {
              const d = DIVISIONS.find((x) => x.key === post.division);
              const accent = d?.color ?? ONE;
              return (
                <Link key={post.slug} href={`/${locale}/blog/${post.slug}`} className="group block">
                  <span className="block h-px w-8 transition-[width] duration-500 group-hover:w-14" style={{ background: accent }} aria-hidden />
                  {d ? (
                    <p className="mt-4 font-mono text-[11px] text-slate">{divisionName(d, locale)}</p>
                  ) : null}
                  <h3 className="font-display mt-2 text-balance text-lg font-bold leading-snug text-platinum transition-opacity group-hover:opacity-80">
                    {bt(post.title, locale)}
                  </h3>
                  <p className="mt-2.5 text-sm leading-relaxed text-chrome-dim">{bt(post.excerpt, locale)}</p>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <FaqSection items={GENERAL_FAQ} locale={locale} accent={ONE} />

      {/* Vision 2030 */}
      <VisionBand locale={locale} />

      {/* CTA */}
      <section>
        <div className="mx-auto max-w-3xl px-5 py-24 text-center sm:px-8">
          <h2 className="font-display text-balance text-3xl font-bold text-platinum sm:text-4xl">{t.ctaTitle}</h2>
          <p className="mt-4 text-chrome-dim">{t.ctaSub}</p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link
              href={`/${locale}/contact`}
              className="rounded-md px-7 py-3 text-sm font-semibold text-void transition-opacity hover:opacity-90"
              style={{ backgroundColor: ONE }}
            >
              {t.ctaBtn}
            </Link>
            <Link
              href={`/${locale}#divisions`}
              className="rounded-md border border-hairline-strong px-7 py-3 text-sm font-semibold text-platinum transition-colors hover:border-ion"
            >
              {t.ctaExplore}
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
