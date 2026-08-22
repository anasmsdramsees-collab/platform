import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { defaultLocale } from "@/lib/i18n/config";
import { siteUrl } from "@/lib/site-config";

// The bare domain redirects into a locale, but Search Console and other
// verifiers fetch this URL directly, so it carries the verification tag too.
export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  verification: { google: "eNLi040aMP52F_djdZ9oVUVoH-JFSGl1oiDVpWZTYWo" },
  alternates: { canonical: `${siteUrl}/${defaultLocale}` },
};

export default function RootPage() {
  redirect(`/${defaultLocale}`);
}
