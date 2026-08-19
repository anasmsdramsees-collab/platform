import type { Metadata } from "next";
import { isLocale, type Locale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n/get-dictionary";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const dict = getDictionary(locale);
  return { title: dict.meta.titleContact, description: dict.meta.description };
}

const EMAIL = "info@syltraone.com";
const WEB = "www.syltraone.com";

export default async function ContactPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const dict = getDictionary(locale);
  const c = dict.contactPage;

  const rows = [
    { label: c.hqLabel, value: c.hqValue, href: undefined },
    { label: c.emailLabel, value: EMAIL, href: `mailto:${EMAIL}` },
    { label: c.webLabel, value: WEB, href: `https://${WEB}` },
    { label: c.corporateLabel, value: c.corporateValue, href: `tel:${c.corporateValue.replace(/[^+\d]/g, "")}` },
  ];

  return (
    <section>
      <div className="mx-auto max-w-3xl px-5 py-24 sm:px-8">
        <p className="font-mono text-[12px] tracking-[0.14em] text-slate uppercase">{c.eyebrow}</p>
        <h1 className="font-display mt-3 text-balance text-4xl font-bold text-platinum sm:text-5xl">
          {c.title}
        </h1>
        <p className="mt-5 max-w-xl text-chrome-dim">{c.subtitle}</p>

        <div className="mt-14 divide-y divide-hairline border-y border-hairline">
          {rows.map((row) => (
            <div key={row.label} className="flex flex-col gap-1 py-6 sm:flex-row sm:items-baseline sm:justify-between">
              <p className="font-mono text-[11px] uppercase tracking-widest text-slate">
                {row.label}
              </p>
              {row.href ? (
                <a
                  href={row.href}
                  dir="ltr"
                  className="text-lg text-platinum transition-colors hover:text-ion"
                >
                  {row.value}
                </a>
              ) : (
                <p className="text-lg text-platinum">{row.value}</p>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
