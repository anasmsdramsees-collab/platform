import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { isLocale, locales, type Locale } from "@/lib/i18n/config";
import { findProductBySlug, allProductSlugs } from "@/lib/products";
import ProductImagePlaceholder from "@/components/product-image-placeholder";
import JsonLd from "@/components/json-ld";
import { siteUrl, siteName } from "@/lib/site-config";
import { pageMetadata } from "@/lib/seo";

export function generateStaticParams() {
  return locales.flatMap((locale) =>
    allProductSlugs().map((slug) => ({ locale, slug }))
  );
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}): Promise<Metadata> {
  const { locale: raw, slug } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const found = findProductBySlug(slug);
  if (!found) return {};
  const copy = locale === "ar" ? found.product.ar : found.product.en;
  return pageMetadata({
    locale,
    path: `/products/${slug}`,
    title: `${found.product.name} | Syltra One`,
    description: copy.tagline,
    image: found.product.images?.[0] ?? "/brand/og-default.jpg",
  });
}

export default async function ProductDetailPage({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}) {
  const { locale: raw, slug } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const found = findProductBySlug(slug);
  if (!found) notFound();

  const { product, category } = found;
  const copy = locale === "ar" ? product.ar : product.en;
  const categoryCopy = locale === "ar" ? category.ar : category.en;

  const t = {
    back: locale === "ar" ? "المنتجات" : "Products",
    imageLabel: locale === "ar" ? "صورة المنتج — قريبًا" : "Product photo — coming soon",
    specs: locale === "ar" ? "المواصفات" : "Specifications",
    category: locale === "ar" ? "الفئة" : "Category",
    viewCategory: locale === "ar" ? "عرض كل" : "View all",
  };

  return (
    <section>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "Product",
          name: product.name,
          description: copy.description,
          brand: { "@type": "Brand", name: siteName },
          category: categoryCopy.name,
          url: `${siteUrl}/${locale}/products/${product.slug}`,
          additionalProperty: copy.specs.map((spec) => ({
            "@type": "PropertyValue",
            name: spec.label,
            value: spec.value,
          })),
        }}
      />
      <div className="mx-auto max-w-5xl px-5 py-14 sm:px-8">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 font-mono text-xs text-slate">
          <Link href={`/${locale}/products`} className="hover:text-platinum">
            {t.back}
          </Link>
          <span aria-hidden="true">/</span>
          <Link href={`/${locale}/products#${category.key}`} className="hover:text-platinum">
            {categoryCopy.name}
          </Link>
        </nav>

        <div className="mt-8 grid grid-cols-1 gap-10 lg:grid-cols-2 lg:gap-16">
          {/* Image */}
          <ProductImagePlaceholder label={t.imageLabel} />

          {/* Content */}
          <div>
            <p className="font-mono text-sm text-platinum">{product.name}</p>
            <h1 className="font-display mt-3 text-balance text-3xl font-bold text-platinum sm:text-4xl">
              {copy.tagline}
            </h1>
            <p className="mt-5 text-chrome-dim">{copy.description}</p>

            <div className="mt-6 flex flex-wrap gap-2">
              {product.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full border border-hairline px-2.5 py-1 font-mono text-[10.5px] text-chrome-dim"
                >
                  {tag}
                </span>
              ))}
            </div>

            <div className="mt-10">
              <p className="font-mono text-[11px] uppercase tracking-widest text-slate">
                {t.specs}
              </p>
              <dl className="mt-3 divide-y divide-hairline border-y border-hairline">
                {copy.specs.map((spec) => (
                  <div
                    key={spec.label}
                    className="flex flex-col gap-1 py-3 sm:flex-row sm:items-baseline sm:justify-between"
                  >
                    <dt className="text-sm text-slate">{spec.label}</dt>
                    <dd className="text-sm text-platinum">{spec.value}</dd>
                  </div>
                ))}
              </dl>
            </div>

            <Link
              href={`/${locale}/products#${category.key}`}
              className="mt-10 inline-block font-mono text-sm text-ion transition-opacity hover:opacity-80"
            >
              {t.viewCategory} {categoryCopy.name} →
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
