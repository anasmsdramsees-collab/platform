import type { Metadata } from "next";
import Link from "next/link";
import { isLocale, type Locale } from "@/lib/i18n/config";
import { pageMetadata } from "@/lib/seo";
import { healthUrl } from "@/lib/site-config";
import { assetPath } from "@/lib/base-path";
import { HEALTH, pickH } from "@/lib/health-content";
import { postsSorted } from "@/lib/health-blog";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const ar = locale === "ar";
  return pageMetadata({
    locale,
    path: "/health/blog",
    title: ar ? "المدونة | سيلترا هيلث" : "Journal | SYLTRA HEALTH",
    description: ar
      ? "مقالات عن الصحة المتصلة والمنزل الذكي وحسّاساته والخصوصية والمتابعة اليومية."
      : "Articles on connected health, the smart home and its sensors, privacy and everyday follow-up.",
    baseUrl: healthUrl,
  });
}

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const ar = locale === "ar";
  const posts = postsSorted();

  return (
    <section className="border-b border-hairline">
      <div className="mx-auto max-w-6xl px-5 py-16 sm:px-8 sm:py-20">
        <p className="font-mono text-[12px] uppercase tracking-[0.16em]" style={{ color: HEALTH.accent }}>
          {ar ? "المدونة" : "Journal"}
        </p>
        <h1 className="font-display mt-4 text-balance text-4xl font-bold text-platinum sm:text-5xl">
          {ar ? "قراءات في الصحة المتصلة." : "Reading on connected health."}
        </h1>

        <div className="mt-12 grid gap-x-10 gap-y-12 sm:grid-cols-2 lg:grid-cols-3">
          {posts.map((p) => (
            <Link key={p.slug} href={`/${locale}/health/blog/${p.slug}`} className="group block">
              {p.image && (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={assetPath(p.image)}
                  alt={pickH(p.title, locale)}
                  className="aspect-[16/10] w-full object-cover"
                />
              )}
              <p className="mt-4 font-mono text-[11px] uppercase tracking-[0.12em] text-slate">
                {pickH(p.category, locale)}
              </p>
              <h2 className="font-display mt-2 text-xl font-bold leading-snug text-platinum transition-colors group-hover:text-chrome-dim">
                {pickH(p.title, locale)}
              </h2>
              <p className="mt-2 text-[15px] leading-relaxed text-chrome-dim">{pickH(p.excerpt, locale)}</p>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
