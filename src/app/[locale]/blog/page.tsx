import type { Metadata } from "next";
import Link from "next/link";
import { isLocale, type Locale } from "@/lib/i18n/config";
import { pageMetadata } from "@/lib/seo";
import { POSTS, bt } from "@/lib/blog";
import { DIVISIONS, divisionName } from "@/lib/divisions";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const title = locale === "ar" ? "المدونة | سيلترا وان" : "Blog | Syltra One";
  const description =
    locale === "ar"
      ? "مقالات وأدلّة عملية في التكييف والمصاعد والأمن والبرمجيات والمنزل الذكي من خبراء سيلترا وان."
      : "Practical guides and articles on HVAC, elevators, security, software and smart homes from Syltra One's experts.";
  return pageMetadata({ locale, path: "/blog", title, description });
}

function fmtDate(iso: string, locale: Locale) {
  const d = new Date(iso);
  return d.toLocaleDateString(locale === "ar" ? "ar-SA" : "en-GB", { year: "numeric", month: "long", day: "numeric" });
}

export default async function BlogIndex({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const ar = locale === "ar";
  const posts = [...POSTS].sort((a, b) => (a.date < b.date ? 1 : -1));

  return (
    <div className="mx-auto max-w-6xl px-5 py-24 sm:px-8">
      <p className="font-mono text-[12px] uppercase tracking-[0.14em] text-slate">{ar ? "المدونة" : "Blog"}</p>
      <h1 className="font-display mt-3 text-balance text-4xl font-bold text-platinum sm:text-5xl">
        {ar ? "أدلّة ومقالات من خبرائنا." : "Guides and articles from our experts."}
      </h1>
      <p className="mt-5 max-w-2xl text-chrome-dim">
        {ar
          ? "معرفة عملية تساعدك على اتخاذ قرار أفضل في التكييف والمصاعد والأمن والبرمجيات والمنزل الذكي."
          : "Practical knowledge to help you decide better on HVAC, elevators, security, software and smart homes."}
      </p>

      <div className="mt-14 grid grid-cols-1 gap-x-8 gap-y-12 sm:grid-cols-2 lg:grid-cols-3">
        {posts.map((post) => {
          const d = DIVISIONS.find((x) => x.key === post.division);
          const accent = d?.color ?? "#BFC6D0";
          return (
            <Link key={post.slug} href={`/${locale}/blog/${post.slug}`} className="group block">
              <span className="block h-px w-8 transition-[width] duration-500 group-hover:w-14" style={{ background: accent }} aria-hidden />
              <div className="mt-4 flex items-center gap-2 font-mono text-[11px] text-slate">
                {d ? (
                  <>
                    <span className="h-2 w-2 rounded-full" style={{ background: accent }} aria-hidden />
                    <span>{divisionName(d, locale)}</span>
                    <span aria-hidden>·</span>
                  </>
                ) : null}
                <span>{fmtDate(post.date, locale)}</span>
              </div>
              <h2 className="font-display mt-3 text-balance text-xl font-bold leading-snug text-platinum transition-opacity group-hover:opacity-80">
                {bt(post.title, locale)}
              </h2>
              <p className="mt-2.5 text-sm leading-relaxed text-chrome-dim">{bt(post.excerpt, locale)}</p>
              <span className="mt-3 inline-flex items-center gap-1.5 text-sm font-semibold" style={{ color: accent }}>
                {ar ? "اقرأ المقال" : "Read article"}
                <span aria-hidden>{ar ? "←" : "→"}</span>
              </span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
