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

  const ld = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "@id": `${healthUrl}/#organization`,
    name: "SYLTRA HEALTH",
    alternateName: ["سيلترا هيلث", "Syltra Health"],
    url: `${healthUrl}/${locale}/health`,
    slogan: pickH(HEALTH_BRAND.tagline, locale),
    description: pickH(page.seoDescription, locale),
    parentOrganization: { "@type": "Organization", name: "Syltra One", url: siteUrl },
    areaServed: { "@type": "Country", name: "Saudi Arabia" },
    knowsLanguage: ["ar", "en"],
    email: "info@syltraone.com",
  };

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
