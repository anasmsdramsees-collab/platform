import type { Metadata } from "next";
import Link from "next/link";
import { isLocale, type Locale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n/get-dictionary";
import { productCatalog } from "@/lib/products";
import { pageMetadata } from "@/lib/seo";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const dict = getDictionary(locale);
  return pageMetadata({ locale, path: "/products", title: dict.meta.titleProducts, description: dict.meta.description });
}

export default async function ProductsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const dict = getDictionary(locale);

  return (
    <div>
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-4xl px-5 py-20 text-center sm:px-8">
          <p className="font-mono text-[12px] tracking-[0.14em] text-slate uppercase">
            {dict.productsPage.eyebrow}
          </p>
          <h1 className="font-display mt-3 text-balance text-4xl font-bold text-platinum sm:text-5xl">
            {dict.productsPage.title}
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-chrome-dim">{dict.productsPage.subtitle}</p>
        </div>
      </section>

      {productCatalog.map((category) => {
        const copy = locale === "ar" ? category.ar : category.en;
        return (
          <section key={category.key} id={category.key} className="scroll-mt-24 border-b border-hairline">
            <div className="mx-auto max-w-6xl px-5 py-16 sm:px-8">
              <div className="max-w-xl">
                <h2 className="font-display text-2xl font-bold text-platinum sm:text-3xl">
                  {copy.name}
                </h2>
                <p className="mt-3 text-chrome-dim">{copy.desc}</p>
              </div>
              <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {category.items.map((product) => {
                  const copy = locale === "ar" ? product.ar : product.en;
                  return (
                    <Link
                      key={product.slug}
                      href={`/${locale}/products/${product.slug}`}
                      className="group rounded-lg border border-hairline p-6 transition-colors hover:border-hairline-strong hover:bg-graphite"
                    >
                      <p className="font-mono text-sm text-platinum">{product.name}</p>
                      <p className="mt-2 text-sm text-chrome-dim">{copy.tagline}</p>
                      <div className="mt-4 flex flex-wrap gap-2">
                        {product.tags.map((tag) => (
                          <span
                            key={tag}
                            className="rounded-full border border-hairline px-2.5 py-1 font-mono text-[10.5px] text-chrome-dim"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                      <p className="mt-4 font-mono text-xs text-ion opacity-0 transition-opacity group-hover:opacity-100">
                        {locale === "ar" ? "التفاصيل ←" : "View details →"}
                      </p>
                    </Link>
                  );
                })}
              </div>
            </div>
          </section>
        );
      })}
    </div>
  );
}
