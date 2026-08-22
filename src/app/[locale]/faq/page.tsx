import type { Metadata } from "next";
import { isLocale, type Locale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n/get-dictionary";
import JsonLd from "@/components/json-ld";
import { siteUrl } from "@/lib/site-config";
import { FaqCards } from "@/components/ui/faq-cards";
import { pageMetadata } from "@/lib/seo";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const dict = getDictionary(locale);
  return pageMetadata({ locale, path: "/faq", title: dict.meta.titleFaq, description: dict.faqPage.subtitle });
}

export default async function FaqPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const dict = getDictionary(locale);
  const f = dict.faqPage;

  return (
    <section>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "FAQPage",
          url: `${siteUrl}/${locale}/faq`,
          mainEntity: f.items.map((item) => ({
            "@type": "Question",
            name: item.q,
            acceptedAnswer: { "@type": "Answer", text: item.a },
          })),
        }}
      />
      <div className="mx-auto max-w-4xl px-5 py-24 sm:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <p className="font-mono text-[12px] tracking-[0.14em] text-slate uppercase">{f.eyebrow}</p>
          <h1 className="font-display mt-3 text-balance text-4xl font-bold text-platinum sm:text-5xl">
            {f.title}
          </h1>
          <p className="mt-5 text-chrome-dim">{f.subtitle}</p>
        </div>

        <div className="mt-14">
          <FaqCards
            items={f.items}
            footerLabel={locale === "ar" ? "عندك سؤال آخر؟" : "Have another question?"}
            footerCta={locale === "ar" ? "تواصل معنا" : "Get in touch"}
            footerHref={`/${locale}/contact`}
          />
        </div>
      </div>
    </section>
  );
}
