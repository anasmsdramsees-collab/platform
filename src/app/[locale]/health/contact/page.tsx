import type { Metadata } from "next";
import { isLocale, type Locale } from "@/lib/i18n/config";
import { pageMetadata } from "@/lib/seo";
import { healthUrl } from "@/lib/site-config";
import { HEALTH } from "@/lib/health-content";
import ContactForm from "@/components/health/contact-form";

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
    path: "/health/contact",
    title: ar ? "التواصل والتجربة المبكرة | سيلترا هيلث" : "Contact & Early Access | SYLTRA HEALTH",
    description: ar
      ? "سجّل اهتمامك بالتجربة المبكرة، أو تواصل معنا لمناقشة شراكة مع عيادة أو مقدم رعاية أو جهة مؤسسية."
      : "Register your interest in early access or contact us to discuss a partnership with a clinic, care provider or organization.",
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

  return (
    <section className="border-b border-hairline">
      <div className="mx-auto grid max-w-6xl gap-12 px-5 py-16 sm:px-8 sm:py-24 lg:grid-cols-[1fr_1.2fr]">
        <div>
          <p className="font-mono text-[12px] uppercase tracking-[0.16em]" style={{ color: HEALTH.accent }}>
            {ar ? "التجربة المبكرة" : "Early Access"}
          </p>
          <h1 className="font-display mt-4 text-balance text-4xl font-bold leading-[1.05] text-platinum sm:text-5xl">
            {ar ? "ابنِ معنا تجربة صحية أكثر اتصالاً." : "Help build a more connected health experience."}
          </h1>
          <p className="mt-6 max-w-md text-base leading-relaxed text-chrome-dim">
            {ar
              ? "سجل اهتمامك بالتجربة المبكرة، أو تواصل معنا لمناقشة شراكة مع عيادة أو مقدم رعاية أو جهة مؤسسية."
              : "Register your interest in early access or contact us to discuss a partnership with a clinic, care provider or organization."}
          </p>
        </div>
        <ContactForm locale={locale} />
      </div>
    </section>
  );
}
