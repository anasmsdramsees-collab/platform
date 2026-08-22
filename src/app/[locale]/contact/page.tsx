import type { Metadata } from "next";
import { isLocale, type Locale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n/get-dictionary";
import { SocialLinks } from "@/components/ui/social-links";
import { pageMetadata } from "@/lib/seo";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const dict = getDictionary(locale);
  return pageMetadata({ locale, path: "/contact", title: dict.meta.titleContact, description: dict.meta.description });
}

const EMAIL = "info@syltraone.com";
const WHATSAPP = "966533826009";
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

  const socials = [
    { name: "WhatsApp", image: "/social/whatsapp.svg", href: `https://wa.me/${WHATSAPP}` },
    { name: "Instagram", image: "/social/instagram.svg", href: "https://www.instagram.com/syltrahome/" },
    { name: "X", image: "/social/x.svg" },
    { name: "LinkedIn", image: "/social/linkedin.svg" },
    { name: "TikTok", image: "/social/tiktok.svg", href: "https://www.tiktok.com/@syltra.home" },
  ];

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

        <div className="mt-16 border-t border-hairline pt-12 text-center">
          <p className="font-mono text-[11px] uppercase tracking-widest text-slate">
            {locale === "ar" ? "تابعنا" : "Follow us"}
          </p>
          <SocialLinks className="mt-10 sm:gap-2" socials={socials} />
        </div>
      </div>
    </section>
  );
}
