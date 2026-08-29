import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { isLocale, locales, type Locale } from "@/lib/i18n/config";
import { pageMetadata } from "@/lib/seo";
import { healthUrl } from "@/lib/site-config";
import { assetPath } from "@/lib/base-path";
import { HEALTH, pickH } from "@/lib/health-content";
import { HEALTH_POSTS } from "@/lib/health-blog";

export function generateStaticParams() {
  return locales.flatMap((locale) => HEALTH_POSTS.map((p) => ({ locale, slug: p.slug })));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}): Promise<Metadata> {
  const { locale: raw, slug } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const post = HEALTH_POSTS.find((p) => p.slug === slug);
  if (!post) return {};
  return pageMetadata({
    locale,
    path: `/health/blog/${slug}`,
    title: `${pickH(post.title, locale)} | SYLTRA HEALTH`,
    description: pickH(post.excerpt, locale),
    image: post.image ?? "/brand/og-default.jpg",
    baseUrl: healthUrl,
  });
}

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}) {
  const { locale: raw, slug } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const ar = locale === "ar";
  const post = HEALTH_POSTS.find((p) => p.slug === slug);
  if (!post) notFound();

  const body = ar ? post.body.ar : post.body.en;
  const ld = {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    headline: pickH(post.title, locale),
    description: pickH(post.excerpt, locale),
    datePublished: post.date,
    inLanguage: ar ? "ar-SA" : "en",
    image: post.image ? `${healthUrl}${post.image}` : undefined,
    articleSection: pickH(post.category, locale),
    author: { "@type": "Organization", name: "SYLTRA HEALTH" },
    publisher: { "@type": "Organization", name: "SYLTRA HEALTH" },
    mainEntityOfPage: `${healthUrl}/${locale}/health/blog/${slug}`,
  };

  return (
    <article className="border-b border-hairline">
      <div className="mx-auto max-w-3xl px-5 py-16 sm:px-8 sm:py-20">
        <Link href={`/${locale}/health/blog`} className="font-mono text-[12px] uppercase tracking-[0.14em] text-slate transition-colors hover:text-platinum">
          {ar ? "← المدونة" : "← Journal"}
        </Link>
        <p className="mt-8 font-mono text-[11px] uppercase tracking-[0.14em]" style={{ color: HEALTH.accent }}>
          {pickH(post.category, locale)}
          {" · "}
          {new Date(post.date).toLocaleDateString(ar ? "ar-SA" : "en-GB", { year: "numeric", month: "long", day: "numeric" })}
        </p>
        <h1 className="font-display mt-3 text-balance text-3xl font-bold leading-tight text-platinum sm:text-4xl">
          {pickH(post.title, locale)}
        </h1>
        <p className="mt-4 text-lg leading-relaxed text-chrome-dim">{pickH(post.excerpt, locale)}</p>
      </div>

      {post.image && (
        <div className="mx-auto max-w-5xl px-5 sm:px-8">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={assetPath(post.image)} alt={pickH(post.title, locale)} className="aspect-[16/9] w-full object-cover" />
        </div>
      )}

      <div className="mx-auto max-w-3xl px-5 py-14 sm:px-8">
        <div className="grid gap-6">
          {body.map((par, k) => (
            <p key={k} className="text-[17px] leading-[1.85] text-chrome">{par}</p>
          ))}
        </div>

        <div className="mt-12 border-t border-hairline pt-8">
          <p className="text-[13px] leading-relaxed text-slate">
            {ar
              ? "هذا المحتوى لدعم الفهم والمتابعة العامة، ولا يمثل تشخيصاً أو علاجاً ولا يستبدل استشارة المختص."
              : "This content supports understanding and general follow-up. It is not a diagnosis or treatment and does not replace professional advice."}
          </p>
        </div>
      </div>

      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(ld) }} />
    </article>
  );
}
