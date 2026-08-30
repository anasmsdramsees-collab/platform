import type { Locale } from "@/lib/i18n/config";
import { siteUrl, healthUrl } from "@/lib/site-config";
import { HEALTH_PAGES } from "@/lib/health-pages";
import { HEALTH, HEALTH_BRAND, pickH } from "@/lib/health-content";
import { HEALTH_FAQ } from "@/lib/health-faq";
import HealthBlocks from "./health-blocks";
import FaqSection from "@/components/faq-section";
import VisionBand from "@/components/vision-band";

/** Renders one HEALTH page from its slug key. `faq` adds the FAQ accordion. */
export default function HealthPageView({
  slugKey,
  locale,
  faq = false,
}: {
  slugKey: string;
  locale: Locale;
  faq?: boolean;
}) {
  const page = HEALTH_PAGES[slugKey];
  const pageUrl = `${healthUrl}/${locale}/health${page.slug}`;
  const homeUrl = `${healthUrl}/${locale}/health`;

  const graph: Record<string, unknown>[] = [
    {
      "@type": "Organization",
      "@id": `${healthUrl}/#organization`,
      name: "SYLTRA HEALTH",
      alternateName: ["سيلترا هيلث", "Syltra Health"],
      url: homeUrl,
      slogan: pickH(HEALTH_BRAND.tagline, locale),
      description: pickH(page.seoDescription, locale),
      parentOrganization: { "@type": "Organization", name: "Syltra One", url: siteUrl },
      areaServed: { "@type": "Country", name: "Saudi Arabia" },
      knowsLanguage: ["ar", "en"],
      email: "info@syltraone.com",
    },
    {
      "@type": "WebSite",
      "@id": `${healthUrl}/#website`,
      url: healthUrl,
      name: "SYLTRA HEALTH",
      inLanguage: locale === "ar" ? "ar-SA" : "en",
      publisher: { "@id": `${healthUrl}/#organization` },
    },
    {
      "@type": "WebPage",
      "@id": `${pageUrl}#webpage`,
      url: pageUrl,
      name: pickH(page.seoTitle, locale),
      description: pickH(page.seoDescription, locale),
      isPartOf: { "@id": `${healthUrl}/#website` },
      inLanguage: locale === "ar" ? "ar-SA" : "en",
    },
    {
      "@type": "BreadcrumbList",
      itemListElement: [
        { "@type": "ListItem", position: 1, name: "SYLTRA HEALTH", item: homeUrl },
        ...(slugKey ? [{ "@type": "ListItem", position: 2, name: pickH(page.seoTitle, locale), item: pageUrl }] : []),
      ],
    },
  ];

  if (slugKey === "app") {
    graph.push({
      "@type": "SoftwareApplication",
      name: "SYLTRA HEALTH",
      applicationCategory: "HealthApplication",
      operatingSystem: "iOS, Android",
      inLanguage: ["ar", "en"],
      publisher: { "@id": `${healthUrl}/#organization` },
      description: pickH(page.seoDescription, locale),
      offers: { "@type": "Offer", price: "0", priceCurrency: "SAR" },
    });
  }

  const ld = { "@context": "https://schema.org", "@graph": graph };

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(ld) }} />
      <HealthBlocks blocks={page.blocks} locale={locale} />
      {(slugKey === "" || slugKey === "about") && <VisionBand locale={locale} accent="var(--color-slate)" />}
      {faq && (
        <FaqSection
          items={HEALTH_FAQ}
          locale={locale}
          accent={HEALTH.accent}
          eyebrow={locale === "ar" ? "الأسئلة الشائعة" : "FAQ"}
          title={locale === "ar" ? "أسئلة يكثر طرحها." : "Questions we hear often."}
        />
      )}
    </>
  );
}
