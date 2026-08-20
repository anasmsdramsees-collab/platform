import type { Metadata } from "next";
import { Unbounded, Manrope, IBM_Plex_Mono, Cairo, IBM_Plex_Sans_Arabic } from "next/font/google";
import "../globals.css";
import { locales, isLocale, type Locale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n/get-dictionary";
import SiteNav from "@/components/site-nav";
import SiteFooter from "@/components/site-footer";
import SinaWidget from "@/components/sina-widget";
import SylaWake from "@/components/syla-wake";
import EnergyReminder from "@/components/energy-reminder";
import JsonLd from "@/components/json-ld";
import { HomeControlsProvider } from "@/lib/home-controls-context";
import { siteUrl, siteName, contactEmail } from "@/lib/site-config";

const unbounded = Unbounded({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["500", "700", "800"],
});

const manrope = Manrope({
  variable: "--font-body",
  subsets: ["latin"],
  weight: ["400", "600", "800"],
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

const cairo = Cairo({
  variable: "--font-display-ar",
  subsets: ["arabic"],
  weight: ["600", "700", "800"],
});

const plexSansArabic = IBM_Plex_Sans_Arabic({
  variable: "--font-body-ar",
  subsets: ["arabic"],
  weight: ["400", "600", "700"],
});

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: rawLocale } = await params;
  const locale: Locale = isLocale(rawLocale) ? rawLocale : "en";
  const dict = getDictionary(locale);
  return {
    title: dict.meta.titleHome,
    description: dict.meta.description,
  };
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale: rawLocale } = await params;
  const locale: Locale = isLocale(rawLocale) ? rawLocale : "en";
  const dir = locale === "ar" ? "rtl" : "ltr";
  const dict = getDictionary(locale);

  return (
    <html
      lang={locale}
      dir={dir}
      className={`${unbounded.variable} ${manrope.variable} ${plexMono.variable} ${cairo.variable} ${plexSansArabic.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-void text-platinum pb-24 sm:pb-0">
        <JsonLd
          data={{
            "@context": "https://schema.org",
            "@type": "Organization",
            name: siteName,
            url: siteUrl,
            logo: `${siteUrl}/brand/logo.png`,
            description: dict.meta.description,
            email: contactEmail,
            address: {
              "@type": "PostalAddress",
              addressLocality: "Riyadh",
              addressCountry: "SA",
            },
          }}
        />
        <HomeControlsProvider>
          <SiteNav locale={locale} dict={dict} />
          <main className="flex-1">{children}</main>
          <SiteFooter locale={locale} dict={dict} />
          <EnergyReminder dict={dict.energyReminder} />
          <SinaWidget dict={dict.sina} locale={locale} />
          <SylaWake locale={locale} />
        </HomeControlsProvider>
      </body>
    </html>
  );
}
