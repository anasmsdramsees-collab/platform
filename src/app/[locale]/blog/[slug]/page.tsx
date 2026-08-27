import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { isLocale, locales, type Locale } from "@/lib/i18n/config";
import { siteUrl } from "@/lib/site-config";
import { pageMetadata } from "@/lib/seo";
import { POSTS, bt } from "@/lib/blog";
import { DIVISIONS, divisionName } from "@/lib/divisions";

export function generateStaticParams() {
  return locales.flatMap((locale) => POSTS.map((p) => ({ locale, slug: p.slug })));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}): Promise<Metadata> {
  const { locale: raw, slug } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const post = POSTS.find((p) => p.slug === slug);
  if (!post) return {};
  return pageMetadata({
    locale,
    path: `/blog/${slug}`,
    title: `${bt(post.title, locale)} | ${locale === "ar" ? "مدونة سيلترا وان" : "Syltra One Blog"}`,
    description: bt(post.excerpt, locale),
    keywords: post.keywords,
  });
}

function fmtDate(iso: string, locale: Locale) {
  return new Date(iso).toLocaleDateString(locale === "ar" ? "ar-SA" : "en-GB", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export default async function ArticlePage({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}) {
  const { locale: raw, slug } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const ar = locale === "ar";
  const post = POSTS.find((p) => p.slug === slug);
  if (!post) notFound();

  const division = DIVISIONS.find((x) => x.key === post.division);
  const accent = division?.color ?? "#BFC6D0";
  const related = POSTS.filter((p) => p.slug !== post.slug).slice(0, 2);

  const ld = [
    {
      "@context": "https://schema.org",
      "@type": "BlogPosting",
      headline: bt(post.title, locale),
      description: bt(post.excerpt, locale),
      datePublished: post.date,
      dateModified: post.date,
      inLanguage: locale === "ar" ? "ar-SA" : "en",
      author: { "@type": "Organization", name: "Syltra One" },
      publisher: { "@type": "Organization", name: "Syltra One" },
      mainEntityOfPage: `${siteUrl}/${locale}/blog/${post.slug}`,
      keywords: post.keywords.join(", "),
    },
    {
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      itemListElement: [
        { "@type": "ListItem", position: 1, name: ar ? "المدونة" : "Blog", item: `${siteUrl}/${locale}/blog` },
        { "@type": "ListItem", position: 2, name: bt(post.title, locale) },
      ],
    },
  ];

  return (
    <article className="mx-auto max-w-3xl px-5 py-24 sm:px-8">
      <nav className="flex items-center gap-2 font-mono text-[11px] text-slate">
        <Link href={`/${locale}/blog`} className="transition-colors hover:text-platinum">
          {ar ? "المدونة" : "Blog"}
        </Link>
        {division ? (
          <>
            <span aria-hidden>/</span>
            <Link href={`/${locale}${division.href}`} className="transition-colors hover:text-platinum" style={{ color: accent }}>
              {divisionName(division, locale)}
            </Link>
          </>
        ) : null}
      </nav>

      <h1 className="font-display mt-5 text-balance text-3xl font-bold leading-[1.2] text-platinum sm:text-4xl">
        {bt(post.title, locale)}
      </h1>
      <p className="mt-4 font-mono text-[11px] text-slate">{fmtDate(post.date, locale)}</p>
      <span className="mt-6 block h-px w-12" style={{ background: accent }} aria-hidden />

      <div className="mt-8 space-y-10">
        {post.body.map((sec, i) => (
          <section key={i}>
            {sec.h ? (
              <h2 className="font-display text-xl font-bold text-platinum sm:text-2xl">{bt(sec.h, locale)}</h2>
            ) : null}
            <div className={`${sec.h ? "mt-4" : ""} space-y-5 text-[15px] leading-[1.9] text-chrome-dim sm:text-base`}>
              {sec.p.map((para, j) => (
                <p key={j}>{bt(para, locale)}</p>
              ))}
            </div>
          </section>
        ))}
      </div>

      {/* CTA */}
      <div className="mt-14 rounded-xl border border-hairline p-8 text-center">
        <p className="text-chrome-dim">
          {ar ? "عندك مشروع أو سؤال؟ فريق سيلترا وان جاهز لمساعدتك." : "Have a project or a question? The Syltra One team is here to help."}
        </p>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
          <Link href={`/${locale}/contact`} className="rounded-md px-6 py-2.5 text-sm font-semibold text-void transition-opacity hover:opacity-90" style={{ background: accent }}>
            {ar ? "تواصل معنا" : "Contact us"}
          </Link>
          {division ? (
            <Link href={`/${locale}${division.href}`} className="rounded-md border border-hairline-strong px-6 py-2.5 text-sm font-semibold text-platinum transition-colors hover:border-ion">
              {ar ? `تعرّف على ${divisionName(division, locale)}` : `Explore ${divisionName(division, locale)}`}
            </Link>
          ) : null}
        </div>
      </div>

      {/* Related */}
      {related.length ? (
        <div className="mt-16 border-t border-hairline pt-10">
          <p className="font-mono text-[12px] uppercase tracking-[0.14em] text-slate">{ar ? "اقرأ أيضًا" : "Read next"}</p>
          <div className="mt-6 grid gap-8 sm:grid-cols-2">
            {related.map((r) => {
              const rd = DIVISIONS.find((x) => x.key === r.division);
              return (
                <Link key={r.slug} href={`/${locale}/blog/${r.slug}`} className="group block">
                  <span className="block h-px w-8 transition-[width] duration-500 group-hover:w-14" style={{ background: rd?.color ?? "#BFC6D0" }} aria-hidden />
                  <h3 className="font-display mt-3 text-balance font-bold leading-snug text-platinum transition-opacity group-hover:opacity-80">
                    {bt(r.title, locale)}
                  </h3>
                </Link>
              );
            })}
          </div>
        </div>
      ) : null}

      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(ld) }} />
    </article>
  );
}
