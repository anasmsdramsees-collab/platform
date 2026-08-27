import type { Locale } from "@/lib/i18n/config";
import { faqText, type QA } from "@/lib/faq";

/**
 * Accessible FAQ accordion (native <details>) plus FAQPage JSON-LD so the
 * questions are eligible for rich results in search.
 */
export default function FaqSection({
  items,
  locale,
  accent = "#4c8dff",
  eyebrow,
  title,
}: {
  items: QA[];
  locale: Locale;
  accent?: string;
  eyebrow?: string;
  title?: string;
}) {
  const ld = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: items.map((it) => ({
      "@type": "Question",
      name: faqText(it.q, locale),
      acceptedAnswer: { "@type": "Answer", text: faqText(it.a, locale) },
    })),
  };

  return (
    <section id="faq" className="scroll-mt-20 border-b border-hairline">
      <div className="mx-auto max-w-4xl px-5 py-24 sm:px-8">
        <p className="font-mono text-[12px] uppercase tracking-[0.14em] text-slate">
          {eyebrow ?? (locale === "ar" ? "الأسئلة الشائعة" : "FAQ")}
        </p>
        <h2 className="font-display mt-3 text-balance text-3xl font-bold text-platinum sm:text-4xl">
          {title ?? (locale === "ar" ? "أسئلة يكثر طرحها." : "Questions we hear often.")}
        </h2>

        <div className="mt-10 border-t border-hairline">
          {items.map((it, i) => (
            <details key={i} className="group border-b border-hairline">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-4 py-5 text-start">
                <span className="font-semibold text-platinum">{faqText(it.q, locale)}</span>
                <span
                  className="relative h-4 w-4 flex-none transition-transform duration-300 group-open:rotate-45"
                  style={{ color: accent }}
                  aria-hidden
                >
                  <span className="absolute left-1/2 top-1/2 h-[2px] w-4 -translate-x-1/2 -translate-y-1/2 bg-current" />
                  <span className="absolute left-1/2 top-1/2 h-4 w-[2px] -translate-x-1/2 -translate-y-1/2 bg-current" />
                </span>
              </summary>
              <p className="pb-5 pe-8 text-sm leading-relaxed text-chrome-dim">{faqText(it.a, locale)}</p>
            </details>
          ))}
        </div>
      </div>

      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(ld) }} />
    </section>
  );
}
